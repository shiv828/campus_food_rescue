import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { FoodListing, WebService } from '../../web-services/web-service';

@Component({
  imports: [RouterLink, FormsModule, DatePipe],
  selector: 'app-businesses',
  styleUrl: './businesses.css',
  templateUrl: './businesses.html',
})
export class Businesses implements OnInit {
  allListings: FoodListing[] = [];
  page = 1;
  loading = false;
  error = '';
  search = '';
  campus = '';
  diet = '';
  availableOnly = false;

  constructor(private webService: WebService, private changeDetector: ChangeDetectorRef) {}

  get campuses() {
    return [...new Set(this.allListings.map(item => item.campus).filter((value): value is string => !!value))].sort();
  }

  get filteredListings() {
    return this.allListings.filter(item =>
      item.food_name.toLowerCase().includes(this.search.trim().toLowerCase())
      && (!this.campus || item.campus === this.campus)
      && (!this.diet || this.tags(item).includes(this.diet))
      && (!this.availableOnly || item.is_available));
  }

  get listings() {
    return this.filteredListings.slice((this.page - 1) * 6, this.page * 6);
  }

  get hasNextPage() { return this.page * 6 < this.filteredListings.length; }

  tags(item: FoodListing): string[] {
    const tags = item.dietary_tags;
    return (Array.isArray(tags) ? tags : (tags || '').split(',')).map(tag => tag.trim().toLowerCase());
  }

  validDeadline(item: FoodListing): boolean {
    return !!item.pickup_deadline && Number.isFinite(Date.parse(item.pickup_deadline));
  }

  deadlinePassed(item: FoodListing): boolean {
    return this.validDeadline(item) && Date.parse(item.pickup_deadline!) <= Date.now();
  }

  ngOnInit() { this.reload(); }

  loadPage(page: number) { this.page = page; }

  reload() {
    this.loading = true;
    this.error = '';
    this.webService.getAllListings().subscribe({
      next: rows => {
        this.allListings = rows;
        this.page = 1;
        this.loading = false;
        this.changeDetector.markForCheck();
      },
      error: () => {
        this.error = 'Could not load food listings. Check that the Flask server is running and try again.';
        this.loading = false;
        this.changeDetector.markForCheck();
      },
    });
  }
}
