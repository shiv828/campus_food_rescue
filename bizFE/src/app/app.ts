import { Component, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { Businesses } from './components/businesses/businesses';
import { Navigation } from './components/navigation/navigation';

@Component({
  imports: [RouterOutlet,Businesses, Navigation],
  selector: 'app-root',
  styleUrl: './app.css',
  templateUrl: './app.html',
})
export class App {
  protected title = "Welcome to Frontend with NG"
}
