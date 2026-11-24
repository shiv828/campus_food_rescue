import { Component, inject, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { FormsModule, NgForm } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { RescueOrders } from '../../services/rescue-orders';

interface ProviderListing {
  _id: string;
  food_name: string;
  listing_status: string;
  quantity_available: number | string;
  pickup_deadline: string;
}

@Component({
  selector: 'app-provider',
  imports: [FormsModule, RouterLink, DatePipe],
  templateUrl: './provider.html',
  styleUrl: './provider.css',
})
export class Provider {
  readonly account = inject(RescueOrders);
  private readonly http = inject(HttpClient);
  private readonly url = 'http://127.0.0.1:5001/api/v1.0/provider/listings';
  readonly rows = signal<ProviderListing[]>([]);
  readonly authorised = signal(false);
  readonly busy = signal(false);
  readonly error = signal('');
  readonly published = signal('');
  email = '';
  password = '';

  constructor() {
    if (this.account.token()) this.load();
  }

  private get options() {
    return { headers: { Authorization: 'Bearer ' + this.account.token() } };
  }

  private failed(err: HttpErrorResponse) {
    this.busy.set(false);
    if (err.status === 401) this.account.logout();
    if (err.status === 401 || err.status === 403) {
      this.authorised.set(false);
      this.rows.set([]);
    }
    this.error.set(err.error?.error || 'Could not reach the food service. Please try again.');
  }

  signIn() {
    this.busy.set(true);
    this.error.set('');
    this.account.login(this.email, this.password).subscribe({
      next: result => {
        this.password = '';
        this.account.setToken(result.token);
        this.load();
      },
      error: err => this.failed(err),
    });
  }

  load() {
    this.busy.set(true);
    this.error.set('');
    this.http.get<ProviderListing[]>(this.url, this.options).subscribe({
      next: rows => {
        this.rows.set(rows);
        this.authorised.set(true);
        this.busy.set(false);
      },
      error: err => this.failed(err),
    });
  }

  publish(form: NgForm) {
    if (form.invalid || this.busy()) return;
    const values = form.value;
    const start = new Date(values.available_from);
    const end = new Date(values.pickup_deadline);
    this.error.set('');
    this.published.set('');
    if (!(end > start && end.getTime() > Date.now())) {
      this.error.set('Choose a future deadline after the collection start.');
      return;
    }
    this.busy.set(true);
    this.http.post<{_id: string}>(this.url, {
      ...values, dietary_tags: values.dietary_tags || '', available_from: start.toISOString(), pickup_deadline: end.toISOString()
    }, this.options).subscribe({
      next: row => {
        this.published.set(row._id);
        form.resetForm();
        this.load();
      },
      error: err => this.failed(err),
    });
  }
}
