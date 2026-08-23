// prompt.js é um módulo de navegador; este .d.ts existe só para o `bun test`
// do Tier 1 poder importá-lo sob `tsc --noEmit`.
export function carregarSemantica(): Promise<any>;
export function resolverMetrica(pergunta: string): any;
export function montarDDL(tabelas: any[], colunas: any, pergunta: string, teto?: number): string;
export function montarJoinHints(tabelas: any[]): string;
export function montarFalseFriends(tabelas: any[], colunas: any): string;
export function montarPrompt(pergunta: string, tabelas: any[], colunas: any): string;
export const SISTEMA: string;
export const TETO_TOKENS: number;
