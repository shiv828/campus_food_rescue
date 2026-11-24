import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { FoodListing } from '../web-services/web-service';

export interface BasketItem { listing: FoodListing; quantity: number; request_id: string; }
export interface Reservation {
  id: string; food_name: string; quantity: number; status: string;
  collection_code: string; pickup_deadline: string;
  pickup_location: string | { building?: string; campus?: string; collection_point?: string };
}

@Injectable({ providedIn: 'root' })
export class RescueOrders {
  private readonly api = 'http://127.0.0.1:5001/api/v1.0';
  readonly basket = signal<BasketItem[]>([]);
  readonly token = signal(sessionStorage.getItem('rescue-token') || '');
  constructor(private http: HttpClient) {}
  add(listing: FoodListing, quantity: number) {
    const existing = this.basket().find(item => item.listing._id === listing._id);
    if (existing) {
      this.basket.update(items => items.map(item => item === existing ? {
        ...item, quantity, request_id: crypto.randomUUID().replaceAll('-', '')
      } : item));
    } else {
      this.basket.update(items => [...items, { listing, quantity, request_id: crypto.randomUUID().replaceAll('-', '') }]);
    }
  }
  remove(id: string) { this.basket.update(items => items.filter(item => item.listing._id !== id)); }
  register(name: string, email: string, password: string) {
    return this.http.post<{message: string}>(this.api + '/customers/register', { name, email, password });
  }
  login(email: string, password: string) {
    return this.http.post<{token: string; name: string}>(this.api + '/customers/login', { email, password });
  }
  setToken(token: string) { this.token.set(token); sessionStorage.setItem('rescue-token', token); }
  logout() { this.setToken(''); }
  private headers() { return { Authorization: 'Bearer ' + this.token() }; }
  reserve(item: BasketItem) {
    return this.http.post<Reservation>(this.api + '/reservations', {
      listing_id: item.listing._id, quantity: item.quantity, request_id: item.request_id
    }, { headers: this.headers() });
  }
  orders() { return this.http.get<Reservation[]>(this.api + '/reservations', { headers: this.headers() }); }
  cancel(id: string) { return this.http.post(this.api + '/reservations/' + id + '/cancel', {}, { headers: this.headers() }); }
}
