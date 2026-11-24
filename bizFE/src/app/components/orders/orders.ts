import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DatePipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { RescueOrders, Reservation } from '../../services/rescue-orders';

@Component({
  selector: 'app-orders', imports: [FormsModule, DatePipe, RouterLink],
  templateUrl: './orders.html', styleUrl: './orders.css'
})
export class Orders {
  readonly store = inject(RescueOrders);
  readonly orders = signal<Reservation[]>([]);
  readonly message = signal('');
  readonly busy = signal(false);
  name = ''; email = ''; password = ''; registering = false;

  constructor() { if (this.store.token()) this.reload(); }

  async authenticate() {
    this.busy.set(true); this.message.set('');
    try {
      if (this.registering) {
        await firstValueFrom(this.store.register(this.name, this.email, this.password));
        this.registering = false;
        this.message.set('Account created. Sign in to reserve food.');
      } else {
        const result = await firstValueFrom(this.store.login(this.email, this.password));
        this.store.setToken(result.token);
        this.password = '';
        await this.reload();
      }
    } catch (error: any) { this.message.set(error.error?.error || (error.status === 0
        ? 'Cannot reach the Flask server. Start the backend on port 5001.'
        : 'The server could not complete this request. Check the Flask terminal for the error.')); }
    finally { this.busy.set(false); }
  }

  async reload() {
    try { this.orders.set(await firstValueFrom(this.store.orders())); }
    catch (error: any) {
      if (error.status === 401) this.store.logout();
      this.message.set(error.error?.error || 'Could not load your reservations.');
    }
  }

  async checkout() {
    this.busy.set(true); this.message.set('');
    let confirmed = 0;
    try {
      for (const item of [...this.store.basket()]) {
        await firstValueFrom(this.store.reserve(item));
        this.store.remove(item.listing._id);
        confirmed++;
      }
      this.message.set('Your reservations are confirmed. Your collection codes appear below.');
    } catch (error: any) {
      this.message.set(confirmed + ' reservations confirmed. ' + (error.error?.error || 'Connection interrupted. Retry to check the remaining reservation.'));
    } finally { await this.reload(); this.busy.set(false); }
  }

  async cancel(id: string) {
    this.busy.set(true);
    try { await firstValueFrom(this.store.cancel(id)); await this.reload(); }
    catch (error: any) { this.message.set(error.error?.error || 'Cancellation failed. Try again.'); }
    finally { this.busy.set(false); }
  }

  location(order: Reservation) {
    const value = order.pickup_location;
    return typeof value === 'string' ? value : [value?.building, value?.campus, value?.collection_point].filter(Boolean).join(' · ');
  }
}
