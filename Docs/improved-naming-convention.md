# Software Project Lifecycle Documentation Naming Convention
## Industry-Standard Best Practices

## 1. Core Principles (Based on Google, Microsoft, Amazon Standards)

### 1.1 Universal Guidelines
- **Language**: Use English for all filenames for global compatibility
- **Characters**: Only `a-z`, `0-9`, `-`, `_` (no spaces, special chars, or mixed languages)
- **Case**: Use kebab-case (lowercase with hyphens) for consistency
- **Length**: Keep filenames under 100 characters
- **Readability**: Self-explanatory without requiring external context

### 1.2 Naming Structure
```
[doc-type]-[component]-[topic]-[version].[extension]
```

**Examples:**
```
adr-001-microservices-architecture-v1.0.md
rfc-002-api-authentication-v2.1.md
spec-frontend-component-library-v1.3.md
guide-deployment-docker-setup-v1.0.md
```

## 2. Document Type Prefixes (Industry Standard)

| Prefix | Full Name | Purpose | Industry Source |
|--------|-----------|---------|-----------------|
| `adr` | Architecture Decision Record | Technical decisions | ThoughtWorks, Microsoft |
| `rfc` | Request for Comments | Proposals & specifications | IETF, Google |
| `spec` | Technical Specification | Detailed technical docs | W3C, AWS |
| `guide` | Implementation Guide | How-to documentation | GitHub, GitLab |
| `runbook` | Operational Runbook | Operations procedures | Netflix, Uber |
| `prd` | Product Requirements | Business requirements | Google, Meta |
| `design` | Design Document | System/UI design | Apple, Figma |
| `test` | Test Documentation | Testing plans/cases | Netflix, Spotify |
| `sop` | Standard Operating Procedure | Process documentation | Amazon, Microsoft |
| `postmortem` | Incident Postmortem | Incident analysis | Google SRE |

## 3. Lifecycle Phase Integration

### 3.1 Directory Structure (Google/Microsoft Style)
```
docs/
├── requirements/           # Business & technical requirements
├── architecture/          # System design & ADRs
├── specifications/        # Technical specs & RFCs
├── implementation/        # Development guides
├── testing/              # Test plans & results
├── deployment/           # Deployment & ops guides
├── operations/           # Runbooks & SOPs
├── postmortems/          # Incident analysis
└── archive/              # Historical documents
```

### 3.2 Component-Based Naming (AWS/Azure Style)
```
[doc-type]-[service/component]-[specific-topic]-[version].md
```

**Examples:**
```
spec-user-service-api-endpoints-v1.2.md
guide-frontend-deployment-pipeline-v1.0.md
adr-003-database-selection-mongodb-v1.0.md
runbook-proxy-service-health-monitoring-v1.1.md
```

## 4. Version Management (Semantic Versioning)

### 4.1 Version Format
- Use semantic versioning: `v[MAJOR].[MINOR]` 
- Major: Breaking changes or complete rewrites
- Minor: Compatible additions or significant updates
- No patch version for documentation (use git history)

### 4.2 Status Management
- **NO status in filename** (use git branches/tags instead)
- Use git workflow: `draft` branch → `review` PR → `main` merge
- Track status via: git tags, PR labels, project boards

## 5. Improved Examples by Category

### 5.1 Architecture & Design
```
adr-001-microservices-vs-monolith-v1.0.md
adr-002-database-sharding-strategy-v1.0.md
design-system-frontend-component-architecture-v2.0.md
spec-api-gateway-routing-rules-v1.1.md
```

### 5.2 Requirements & Planning
```
prd-user-management-system-v1.0.md
prd-proxy-scanning-service-v2.0.md
spec-integration-third-party-apis-v1.0.md
rfc-001-authentication-authorization-v1.0.md
```

### 5.3 Implementation & Testing
```
guide-frontend-development-setup-v1.0.md
guide-backend-api-implementation-v1.2.md
test-integration-test-strategy-v1.0.md
test-performance-benchmarking-plan-v1.0.md
```

### 5.4 Operations & Deployment
```
runbook-production-deployment-v1.1.md
runbook-incident-response-escalation-v1.0.md
guide-docker-containerization-v1.0.md
sop-database-backup-recovery-v1.0.md
```

## 6. Metadata & Cross-References

### 6.1 Document Headers (YAML Frontmatter)
```yaml
---
title: "User Service API Specification"
type: "specification"
version: "1.2"
status: "approved"
author: "Platform Team"
reviewers: ["tech-lead", "senior-dev"]
created: "2025-01-15"
updated: "2025-02-10"
related: ["adr-001-microservices", "guide-api-development"]
tags: ["api", "backend", "user-service"]
---
```

### 6.2 Cross-Reference Format
- Link related docs: `See also: [adr-001-microservices](../architecture/adr-001-microservices-v1.0.md)`
- Use consistent internal linking with relative paths

## 7. Key Improvements Over Current Approach

### 7.1 Issues with Original Naming
❌ **Problems Identified:**
1. **Mixed Languages**: Chinese-English mixing reduces global compatibility
2. **Complex Structure**: `PH1_PRD_代理管理系統_v1.0.0(已定稿).md` is too verbose
3. **Status in Filename**: `(草稿)`, `(審核中)` should use git workflow instead
4. **Phase Codes**: `PH0-PH5` not industry standard
5. **Inconsistent Versioning**: Mixing dates and semantic versions

### 7.2 Industry Best Practices Applied
✅ **Improvements:**
1. **English-Only**: Global team compatibility
2. **Standardized Prefixes**: `adr`, `rfc`, `spec` recognized worldwide
3. **Git-Based Status**: Use branches/PRs instead of filename status
4. **Component-Based**: Focuses on what system/service the doc covers
5. **Semantic Versioning**: Consistent `v1.0` format

## 8. Migration Strategy

### 8.1 Filename Conversion Examples
```
# Old → New
PH1_PRD_代理管理系統_v1.0.0(已定稿).md
→ prd-proxy-management-system-v1.0.md

PH2_API設計_Proxy與ETL_v1.0.0(已定稿).md  
→ spec-proxy-service-api-design-v1.0.md

PH3_部署指南_Docker與Compose_v1.0.0(已定稿).md
→ guide-deployment-docker-compose-v1.0.md
```

### 8.2 Directory Restructure
```
# Old Structure
Docs/
  PH0_Initiation/
  PH1_Requirements_Design/
  PH2_Development_Testing/

# New Structure  
docs/
  requirements/
  architecture/
  specifications/
  implementation/
  operations/
```

## 9. Automation & Tooling

### 9.1 Filename Validation Regex
```regex
^(adr|rfc|spec|guide|runbook|prd|design|test|sop|postmortem)-[a-z0-9-]+-v\d+\.\d+\.(md|pdf|png|drawio)$
```

### 9.2 Template Generation Script
```bash
# Generate new document template
./scripts/new-doc.sh spec user-service api-endpoints
# Creates: spec-user-service-api-endpoints-v1.0.md
```

### 9.3 Git Hooks
```bash
#!/bin/bash
# pre-commit hook to validate filenames
if [[ ! $filename =~ $NAMING_REGEX ]]; then
  echo "Error: Filename doesn't follow naming convention"
  exit 1
fi
```

## 10. Quick Reference

### 10.1 Common Document Types
| Type | Use Case | Example |
|------|----------|---------|
| `adr` | Architecture decisions | `adr-001-database-selection-v1.0.md` |
| `prd` | Product requirements | `prd-user-authentication-v2.0.md` |
| `spec` | Technical specifications | `spec-api-gateway-routing-v1.1.md` |
| `guide` | Implementation how-tos | `guide-frontend-setup-v1.0.md` |
| `runbook` | Operational procedures | `runbook-incident-response-v1.0.md` |

### 10.2 Version Guidelines
- `v1.0`: Initial version
- `v1.1`: Minor updates, additions
- `v2.0`: Major changes, breaking updates
- Use git tags for release versions

---

**This naming convention follows industry standards from:**
- Google Engineering Practices
- Microsoft Azure Documentation Standards  
- AWS Well-Architected Framework
- GitHub/GitLab Documentation Guidelines
- ThoughtWorks Technology Radar

**Benefits:**
- ✅ Global team compatibility
- ✅ Tool integration support
- ✅ Searchable and sortable
- ✅ Version control friendly
- ✅ Industry standard compliance