// Shared interfaces for the Firewall Portal
export interface User {
    id?: number;
    email: string;
    display_name: string;
    role: string;
    workload?: string;
    workload_type?: string;
    is_active?: boolean;
}

export interface FirewallRule {
    id?: number;
    name: string;
    description?: string;
    landing_zone: string;
    subscription_id?: string;
    resource_group?: string;
    firewall_policy?: string;
    rule_collection_name: string;
    priority?: number;
    action?: string;
    source_addresses?: string[];
    destination_addresses?: string[];
    destination_ports?: string[];
    destination_fqdns?: string[];
    protocols?: string[];
    category?: string;
    workload?: string;
    workload_type?: string;
    environment?: string;
    status?: string;
    is_active?: boolean;
    created_by?: string;
    created_at?: string;
    updated_at?: string;
    approved_at?: string;
    approved_by?: string;
    submitted_for_approval_at?: string;
    tags?: Tag[];
    approvers?: User[];
    approvals?: ApprovalRecord[];
}

export interface Tag {
    id?: number;
    name: string;
    color?: string;
}

export interface ApprovalRecord {
    id?: number;
    rule_id?: number;
    approver_role: string;
    approver_name?: string;
    status: string;
    notes?: string;
    approved_at?: string;
}

export interface AuditLog {
    id?: number;
    entity_type: string;
    entity_id?: number;
    action: string;
    old_values?: Record<string, unknown>;
    new_values?: Record<string, unknown>;
    user_id?: string;
    username?: string;
    ip_address?: string;
    timestamp?: string;
    extra_data?: Record<string, unknown>;
}

export interface ApiResponse<T> {
    items?: T[];
    total?: number;
    page?: number;
    per_page?: number;
}

export interface LoginResponse {
    access_token: string;
    token_type: string;
    refresh_token: string;
    expires_in: number;
    user: User;
}

export interface RuleFilter {
    landing_zone?: string;
    status?: string[];
    action?: string[];
    category?: string[];
    workload?: string;
    environment?: string;
    search?: string;
    priority_min?: number;
    priority_max?: number;
    sort_by?: string;
    sort_order?: string;
}

export interface ApprovalStatus {
    rule_id: number;
    approvals: ApprovalStatusItem[];
}

export interface ApprovalStatusItem {
    id?: number;
    approver_role: string;
    approver_name?: string;
    status: string;
    notes?: string;
    approved_at?: string;
}

export interface PendingApproval {
    approval_record_id?: number;
    rule_id?: number;
    rule_name: string;
    rule_status?: string;
    approver_role: string;
    status: string;
    notes?: string;
    created_at?: string;
}

export interface Statistics {
    total?: number;
    by_status?: Record<string, number>;
    by_action?: Record<string, number>;
    by_landing_zone?: Record<string, number>;
}