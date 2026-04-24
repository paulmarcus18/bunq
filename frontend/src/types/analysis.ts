export type DocumentType =
  | "fine"
  | "invoice"
  | "utility_bill"
  | "tax_letter"
  | "subscription_change"
  | "refund"
  | "scam_risk"
  | "unknown";

export type Urgency = "low" | "medium" | "high";
export type RiskLevel = "low" | "medium" | "high";
export type RecommendedAction =
  | "pay_now"
  | "schedule_payment"
  | "request_money"
  | "mark_suspicious"
  | "review_manually"
  | "ignore";

export interface AnalysisResponse {
  document_type: DocumentType;
  sender: string | null;
  recipient_name: string | null;
  iban: string | null;
  amount: number | null;
  currency: string;
  due_date: string | null;
  payment_reference: string | null;
  urgency: Urgency;
  risk_level: RiskLevel;
  recommended_action: RecommendedAction;
  summary: string;
  reasoning: string;
  confidence: number;
  action_required: boolean;
  direct_debit_detected: boolean;
  decision_reasons: string[];
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
    recipient: string | null;
    iban: string | null;
    due_date: string | null;
    reference: string | null;
    description: string | null;
  };
}
