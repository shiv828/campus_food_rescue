import { FormsModule } from '@angular/forms';
import { RescueOrders } from '../../../services/rescue-orders';
import { DatePipe } from '@angular/common';
import { Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { catchError, map, of, startWith, switchMap } from 'rxjs';
import { FoodListing, WebService } from '../../../web-services/web-service';

interface ListingState {
  listing?: FoodListing;
  error?: string;
}

@Component({
  imports: [RouterLink, DatePipe, FormsModule],
  selector: 'app-business',
  styleUrl: './business.css',
  templateUrl: './business.html',
})
export class Business {
  readonly cart = inject(RescueOrders);
  quantity = 1;
  added = false;
  canReserve(listing: FoodListing) {
    return listing.is_available && !!listing.pickup_deadline && Date.parse(listing.pickup_deadline) > Date.now();
  }
  addToBasket(listing: FoodListing) {
    if (this.canReserve(listing) && Number.isInteger(this.quantity) && this.quantity >= 1 && this.quantity <= 10 && this.quantity <= Number.parseFloat(String(listing.quantity_available))) {
      this.cart.add(listing, this.quantity);
      this.added = true;
    }
  }
  private readonly route = inject(ActivatedRoute);
  private readonly webService = inject(WebService);

  validDeadline(value?: string): boolean {
    return !!value && Number.isFinite(Date.parse(value));
  }

  readonly state = toSignal(this.route.paramMap.pipe(
    switchMap((params) => {
      const id = params.get('id');
      if (!id) {
        return of<ListingState>({ error: 'Missing food listing ID.' });
      }
      return this.webService.getBusiness(id).pipe(
        map((listing): ListingState => ({ listing })),
        catchError(() => of<ListingState>({ error: 'Could not load this food listing.' })),
        startWith({} as ListingState),
      );
    }),
  ), { initialValue: {} as ListingState });
}
