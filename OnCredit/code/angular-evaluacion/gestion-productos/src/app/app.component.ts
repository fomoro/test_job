import { Component } from '@angular/core';
import { AuthService } from './services/auth.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  title = 'gestion-productos';

  constructor(private authService: AuthService, private router: Router) {}

  // Verificar si el usuario está autenticado
  isAuthenticated(): boolean {
    return this.authService.isAuthenticated();
  }

  // Método para cerrar sesión
  logout(): void {
    this.authService.logout(); // Elimina el token
    this.router.navigate(['/login']); // Redirige a la página de login
  }
}
