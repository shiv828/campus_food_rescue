import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { RouterLink } from '@angular/router';
import { DatePipe } from '@angular/common';
import { FoodListing, WebService } from '../../web-services/web-service';

@Component({
  imports: [RouterLink, DatePipe],
  selector: 'app-home',
  styleUrl: './home.css',
  templateUrl: './home.html',
})
export class Home implements OnInit {
  meals: FoodListing[] = [];
  collected = 0;
  providers = 0;
  loading = true;
  error = '';

  constructor(private webService: WebService, private changeDetector: ChangeDetectorRef) {}

  ngOnInit() {
    this.webService.getAllListings().subscribe({
      next: rows => {
        this.meals = rows.filter(item => item.is_available).slice(0, 3);
        this.collected = rows.filter(item => item.listing_status?.toLowerCase() === 'collected').length;
        this.providers = new Set(rows.map(item => item.provider_id).filter(Boolean)).size;
        this.loading = false;
        this.changeDetector.markForCheck();
      },
      error: () => {
        this.error = 'Food listings are temporarily unavailable. Try the listings page again shortly.';
        this.loading = false;
        this.changeDetector.markForCheck();
      },
    });
  }
}
