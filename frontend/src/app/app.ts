import { Component } from '@angular/core';
import { AnalyzerComponent } from './pages/analyzer/analyzer.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [AnalyzerComponent],
  template: '<app-analyzer></app-analyzer>'
})
export class App {}
