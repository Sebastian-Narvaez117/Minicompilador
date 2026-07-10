import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormsModule, ReactiveFormsModule, UntypedFormControl, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { LexicalService } from '../../core/services/lexical.service';
import { AnalyzeResponse, Metrics, PhaseResult } from '../../models/response.model';

@Component({
  selector: 'app-analyzer',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    MatButtonModule,
    MatCardModule,
    MatIconModule,
    MatFormFieldModule,
    MatInputModule,
    MatSnackBarModule,
  ],
  templateUrl: './analyzer.component.html',
  styleUrls: ['./analyzer.component.scss']
})
export class AnalyzerComponent {
  private readonly lexicalService = inject(LexicalService);
  private readonly snackBar = inject(MatSnackBar);

  protected readonly sourceControl = new UntypedFormControl(
    '',
    { validators: [Validators.required, Validators.minLength(3)] }
  );

  protected readonly examples = [
    'convertir 100 celsius a fahrenheit',
    'convertir 32 fahrenheit a celsius',
    'convertir 300 kelvin a celsius',
    'convertir 212 °F a centigrados',
  ] as const;

  protected readonly unitGroups = [
    { name: 'Celsius', synonyms: 'celsius, centigrados, °C', color: '#5da6ff' },
    { name: 'Fahrenheit', synonyms: 'fahrenheit, °F', color: '#ffb74d' },
    { name: 'Kelvin', synonyms: 'kelvin, K', color: '#ce93d8' },
  ] as const;

  protected readonly response = signal<AnalyzeResponse | null>(null);
  protected readonly httpStatus = signal<number | null>(null);
  protected readonly isSubmitting = signal(false);
  protected readonly errorMessage = signal<string | null>(null);

  protected analyze(): void {
    if (this.sourceControl.invalid) {
      this.sourceControl.markAsTouched();
      return;
    }

    const sourceValue = this.sourceControl.value?.trim();
    if (!sourceValue) return;

    this.isSubmitting.set(true);
    this.errorMessage.set(null);
    this.httpStatus.set(null);

    this.lexicalService.analyze(sourceValue).subscribe({
      next: (result) => {
        this.response.set(result);
        this.isSubmitting.set(false);
      },
      error: (error) => {
        const status = error.status;
        const body = error.error;
        this.httpStatus.set(status);

        if (status === 503) {
          this.response.set(body);
          this.errorMessage.set(body?.semantic?.message || 'Servicio semántico no disponible');
        } else if (status === 502) {
          this.response.set(body);
          this.errorMessage.set(body?.semantic?.message || 'Error en servicio semántico');
        } else if (status === 401 || status === 400) {
          this.errorMessage.set(body?.error || 'Solicitud inválida');
        } else {
          this.errorMessage.set(error.message || 'Error al conectar con el servidor');
        }

        this.isSubmitting.set(false);
        this.snackBar.open(this.errorMessage()!, 'Cerrar', { duration: 5000 });
      }
    });
  }

  protected fillExample(text: string): void {
    this.sourceControl.setValue(text);
    this.response.set(null);
    this.errorMessage.set(null);
  }

  protected getSyntaxIcon(syntax: PhaseResult | undefined): string {
    if (!syntax) return 'hourglass_empty';
    return syntax.valid ? 'check_circle' : 'error_outline';
  }

  protected getSemanticIcon(semantic: PhaseResult | undefined): string {
    if (!semantic) return 'hourglass_empty';
    if (semantic.status === 'unavailable') return 'cloud_off';
    if (semantic.status === 'error') return 'error';
    return semantic.valid ? 'check_circle' : 'warning_amber';
  }

  protected phaseStatus(phase: PhaseResult | undefined): string {
    if (!phase) return 'pending';
    if (phase.status === 'unavailable') return 'unavailable';
    if (phase.status === 'error') return 'error';
    return phase.valid ? 'ok' : 'fail';
  }

  protected phaseLabel(phase: PhaseResult | undefined): string {
    if (!phase) return 'Esperando...';
    if (phase.status === 'unavailable') return 'No disponible';
    if (phase.status === 'error') return 'Error';
    if (phase.valid) return 'Correcto';
    return 'Inválido';
  }

  protected formatMs(ms: number | undefined): string {
    if (ms === undefined || ms === null) return '—';
    return ms < 1 ? `< 1 ms` : `${ms.toFixed(1)} ms`;
  }

  protected formatToken(token: string): string {
    if (!token) return '—';
    return token
      .replace(/_/g, ' ')
      .toLowerCase()
      .replace(/\b\w/g, c => c.toUpperCase());
  }
}
