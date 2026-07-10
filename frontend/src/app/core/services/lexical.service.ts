import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable, signal } from '@angular/core';
import { catchError, Observable, throwError } from 'rxjs';
import { AnalyzeResponse } from '../../models/response.model';

@Injectable({
  providedIn: 'root'
})
export class LexicalService {
  private readonly endpoint = '/api/analyze';
  public readonly isLoading = signal(false);

  constructor(private http: HttpClient) {}

  analyze(source: string): Observable<AnalyzeResponse> {
    this.isLoading.set(true);
    return this.http.post<AnalyzeResponse>(this.endpoint, { source }).pipe(
      catchError((error: HttpErrorResponse) => {
        return throwError(() => error);
      })
    );
  }
}
