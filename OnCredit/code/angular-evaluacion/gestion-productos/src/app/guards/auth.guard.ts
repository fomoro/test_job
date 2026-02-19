import { Injectable } from '@angular/core';
import { CanActivate, ActivatedRouteSnapshot, RouterStateSnapshot, Router } from '@angular/router';
import { Observable } from 'rxjs';
import { AuthService } from '../services/auth.service';

@Injectable({
  providedIn: 'root'
})
export class AuthGuard implements CanActivate {

  constructor(private authService: AuthService, private router: Router) {}

  canActivate(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): Observable<boolean> | Promise<boolean> | boolean {
    const token = localStorage.getItem('authToken');  // Cambiado 'token' a 'authToken'

    if (token) {
      // Si el token existe, permitimos el acceso
      return true;
    } else {
      // Si no hay token, redirigimos a la página de login
      this.router.navigate(['/login']);
      return false;
    }
  }
}
