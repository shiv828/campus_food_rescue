import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { expand, map, reduce, EMPTY } from 'rxjs';

export interface FoodListing {
    _id: string;
    food_name: string;
    photo_url?: string;
    description?: string;
    pickup_deadline?: string;
    dietary_tags?: string[] | string;
    provider_id?: string;
    campus?: string;
    is_available: boolean;
    pickup_location?: string;
    quantity_available?: number | string;
    listing_status?: string;
}

type ApiFoodListing = Omit<FoodListing, 'pickup_location' | 'photo_url' | 'is_available'> & {
    pickup_location?: string | {
        building?: string;
        campus?: string;
        collection_point?: string;
    } | null;
};

const mealPhotos = new Map([
    ['vegetable lentil curry with rice', 'lentil-curry-rice'],
    ['cheese and tomato panini', 'cheese-tomato-panini'],
    ['tomato and basil soup', 'tomato-basil-soup'],
    ['seasonal fruit cups', 'seasonal-fruit-cups'],
    ['bakery pastry selection', 'bakery-pastries'],
    ['chickpea salad boxes', 'chickpea-salad'],
    ['roasted vegetable wraps', 'roasted-vegetable-wraps'],
    ['jacket potatoes with baked beans', 'jacket-potatoes-beans'],
    ['vegetable pasta bake', 'vegetable-pasta-bake'],
    ['falafel wraps', 'falafel-wraps'],
    ['rice and bean bowls', 'rice-bean-bowls'],
    ['banana bread slices', 'banana-bread'],
    ['sandwich selection', 'sandwich-selection'],
    ['garden salad bowls', 'garden-salad'],
    ['vegetable stir-fry with noodles', 'vegetable-stir-fry'],
    ['oat and berry breakfast pots', 'oat-berry-pots'],
    ['cheese scones', 'cheese-scones'],
    ['jacket potatoes with tuna', 'jacket-potatoes-tuna'],
    ['vegetable samosas', 'vegetable-samosas'],
    ['vegetarian pizza slices', 'vegetarian-pizza'],
    ['vegetable curry', 'vegetable-curry'],
]);

function mealPhotoUrl(name: string): string | undefined {
    const slug = mealPhotos.get(name.trim().toLowerCase());
    return slug ? 'food-photos/' + slug + '.jpg' : undefined;
}

function formatListing(listing: ApiFoodListing): FoodListing {
    const location = listing.pickup_location;
    const pickupLocation = typeof location === 'string'
        ? location.trim()
        : [location?.building, location?.campus, location?.collection_point]
            .map(part => part?.trim())
            .filter(Boolean)
            .join(' · ');

    const deadline = listing.pickup_deadline ? Date.parse(listing.pickup_deadline) : NaN;
    const quantity = Number.parseFloat(String(listing.quantity_available));
    return {
        ...listing,
        campus: typeof location === 'object' && location ? location.campus : undefined,
        is_available: listing.listing_status?.toLowerCase() === 'available'
            && Number.isFinite(deadline) && deadline > Date.now() && quantity > 0,
        pickup_location: pickupLocation || 'Pickup location unavailable',
        photo_url: mealPhotoUrl(listing.food_name),
    };
}

@Injectable({ providedIn: 'root' })
export class WebService {
    readonly pageSize = 3;
    private readonly listingsUrl = 'http://127.0.0.1:5001/api/v1.0/listings';

    constructor(private http: HttpClient) {}

    getBusinesses(page: number) {
        return this.http.get<ApiFoodListing[]>(this.listingsUrl, {
            params: { pn: page, ps: this.pageSize },
        }).pipe(map(listings => listings.map(formatListing)));
    }

    getAllListings() {
        const size = 100;
        const fetchPage = (page: number) => this.http.get<ApiFoodListing[]>(this.listingsUrl, {
            params: { pn: page, ps: size },
        });
        return fetchPage(1).pipe(
            expand((rows, index) => rows.length === size ? fetchPage(index + 2) : EMPTY),
            reduce((all, rows) => all.concat(rows), [] as ApiFoodListing[]),
            map(rows => rows.map(formatListing).sort((a, b) => Number(b.is_available) - Number(a.is_available))),
        );
    }

    getBusiness(id: string) {
        return this.http.get<ApiFoodListing>(this.listingsUrl + '/' + encodeURIComponent(id))
            .pipe(map(formatListing));
    }
}
