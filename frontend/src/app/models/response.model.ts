import { Token } from './token.model';

export interface PhaseResult {
  valid: boolean;
  message?: string;
  status?: string;
  tree?: unknown;
  details?: Record<string, unknown>;
  rule?: string;
}

export interface Metrics {
  automata_ms: number;
  llm_ms: number;
  total_ms: number;
}

export interface ConversionResult {
  value: number;
  from: { unit: string; value: number };
  to: { unit: string; value: number };
  formula: string;
  error?: string;
}

export interface AnalyzeResponse {
  source: string;
  valid: boolean;
  status: string;
  message: string;
  automata: Token[];
  llm: Token[];
  merged: Token[];
  lexical: { automata: Token[]; llm: Token[]; merged: Token[] };
  syntax?: PhaseResult;
  semantic?: PhaseResult;
  conversion?: ConversionResult;
  metrics?: Metrics;
}
