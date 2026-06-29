export interface Case {
  id: string;
  case_number: string;
  title: string;
  description?: string;
  case_type: string;
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  status: 'DRAFT' | 'ACTIVE' | 'ON_HOLD' | 'CLOSED' | 'ARCHIVED';
  jurisdiction?: string;
  filing_date?: string;
  meta_data?: any;
  created_at: string;
  updated_at: string;
}

export interface TimelineEvent {
  date: string;
  event: string;
  source_document: string;
  importance: string;
}

export interface EvidenceItem {
  fact: string;
  status: string;
  importance: string;
  reliability: string;
  source: string;
}

export interface Contradiction {
  description: string;
  source_a: string;
  source_b: string;
  impact: string;
}

export interface LegalIssue {
  issue_type: string;
  description: string;
  severity: string;
}

export interface RiskScores {
  litigation_risk: number;
  evidence_strength: number;
  urgency: number;
  settlement_probability: number;
  employer_defense: number;
  explanation: string;
}

export interface EvidenceCitation {
  document: string;
  section?: string;
  page?: string;
  chunk_id?: string;
  strength: string;
  quote: string;
}

export interface RecommendationJustification {
  why_appropriate: string;
  why_now: string;
  supporting_facts?: string[];
  weakening_facts?: string[];
  required_assumptions?: string[];
}

export interface Counterargument {
  argument: string;
  strength: string;
  likelihood_of_success: string;
  supporting_evidence?: string[];
  contradicting_evidence?: string[];
}

export interface DetailedAlternativeStrategy {
  strategy: string;
  advantages?: string[];
  disadvantages?: string[];
  estimated_success: string;
  when_to_choose: string;
  trade_offs: string;
}

export interface DetailedApplicableLaw {
  statute: string;
  why_it_applies: string;
  triggering_facts?: string[];
  confidence: string;
  jurisdiction: string;
}

export interface DetailedPrecedent {
  case_name: string;
  court: string;
  year: string;
  similarity_score: string;
  reason_it_applies: string;
}

export interface Recommendation {
  id: string;
  case_id: string;
  recommendation_type: string;
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high' | 'urgent' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  priority_explanation?: string;
  confidence_score: number;
  confidence_explanation?: string;
  evidence_completeness_score?: string;
  reasoning?: string;
  justification?: RecommendationJustification;
  supporting_evidence?: EvidenceCitation[];
  counterarguments?: Counterargument[];
  alternative_actions?: any[];
  alternative_strategies?: DetailedAlternativeStrategy[];
  executive_summary?: string;
  missing_evidence?: string[];
  applicable_laws?: string[];
  detailed_applicable_laws?: DetailedApplicableLaw[];
  relevant_precedents?: string[];
  detailed_precedents?: DetailedPrecedent[];
  legal_risks?: string[];
  next_best_actions?: string[];
  expected_outcome?: string;
  urgency?: string;
  rank?: number;
  meta_data?: any;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'IMPLEMENTED' | 'pending_review';
  created_at: string;
  updated_at: string;
}

export interface PlannerExecution {
  id: string;
  case_id?: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
  workflow_type: string;
  planned_agents: string[];
  executed_agents: string[];
  skipped_agents: string[];
  failed_agents: string[];
  execution_order?: number[];
  agent_outputs?: Record<string, any>;
  execution_metadata?: Record<string, any>;
  start_time?: string;
  end_time?: string;
  total_duration_ms?: number;
  created_at: string;
  updated_at: string;
}

export interface Memory {
  id: string;
  memory_type: 'SHORT_TERM' | 'LONG_TERM' | 'CONVERSATION' | 'CASE';
  content: Record<string, any>;
  metadata?: Record<string, any>;
  case_id?: string;
  session_id?: string;
  created_at: string;
  updated_at: string;
}

export interface Agent {
  agent_id: string;
  name: string;
  description: string;
  capabilities: string[];
  version: string;
  status: 'ACTIVE' | 'INACTIVE';
  metadata?: Record<string, any>;
}

export interface Tool {
  tool_id: string;
  name: string;
  description: string;
  tool_type: string;
  version: string;
  status: 'ACTIVE' | 'INACTIVE';
  metadata?: Record<string, any>;
}

export interface Feedback {
  id: string;
  case_id?: string;
  recommendation_id?: string;
  feedback_type: 'APPROVAL' | 'REJECTION' | 'MODIFICATION' | 'COMMENT';
  content: string;
  user_id?: string;
  created_at: string;
}
