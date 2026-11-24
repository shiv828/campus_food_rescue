import { Routes } from '@angular/router';
import { Orders } from './components/orders/orders';
import { Home } from './components/home/home';
import { Businesses } from './components/businesses/businesses';
import { Business } from './components/businesses/business/business';

// ng g c business
export const routes: Routes = [
    { path: "provider", loadComponent: () => import("./components/provider/provider").then(module => module.Provider) },
    { path: "orders", component: Orders },
    {
        path: '',
        component: Home
    },
    {
        path: 'businesses',
        component: Businesses
    },
    {
        path: 'businesses/:id',
        component: Business
    }
];
