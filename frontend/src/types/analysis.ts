export type DocumentType =
  | "invoice"
  | "utility_bill"
  | "tax_letter"
  | "fine"
  | "phishing_email"
  | "impersonation_scam"
  | "fake_invoice"
  | "unknown";

export type RecommendedAction =
  | "pay_now"
  | "schedule_payment"
  | "review_manually"
  | "ignore";

export interface AnalysisResponse {
  document_type: DocumentType;
  issuer_name: string | null;
  beneficiary_name: string | null;
  beneficiary_iban: string | null;
  amount: number | null;
  currency: string;
  due_date: string | null;
  payment_reference: string | null;
  payment_description: string | null;
  manual_payment_required: boolean;
  auto_debit_detected: boolean;
  is_suspicious: boolean;
  phishing_signals: string[];
  recommended_action: RecommendedAction;
  summary: string;
  action_required: boolean;
  transcript: string | null;
  input_modality: "document" | "voice";
  trust_score: number;
  risk_level: "safe" | "caution" | "blocked";
  trust_reasons: { text: string; polarity: "positive" | "negative" }[];
  trust_breakdown: {
    issuer_authenticity: number;
    urgency_pressure: number;
    payment_detail_completeness: number;
    modality_risk: number;
  };
}

export interface BunqAccountSummary {
  id: string;
  description: string;
  balance: string;
  currency: string;
  iban: string | null;
}

export interface BunqAccountsResponse {
  mode: string;
  user_id: string;
  accounts: BunqAccountSummary[];
}

export interface ConfirmActionResponse {
  success: boolean;
  message: string;
  bunq_user_id: string;
  account_used: string;
  account_iban: string | null;
  prepared_action: {
    type: RecommendedAction;
    bunq_action_type: string;
    execution_state: string;
    bunq_action_id: string | null;
    amount: number | null;
    currency: string;
    beneficiary_name: string | null;
    beneficiary_iban: string | null;
    due_date: string | null;
    reference: string | null;
    description: string | null;
    bunq_endpoint: string | null;
    bunq_mode: string;
    trust_score: number;
    risk_level: "safe" | "caution" | "blocked";
  };
}
