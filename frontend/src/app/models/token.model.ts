export interface Token {
  token: string;
  lexeme: string;
  position: number;
  source: 'AFD' | 'LLM' | string;
}
