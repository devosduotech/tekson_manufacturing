# MES Release Checklist

**Document Type:** Deployment Checklist  
**Version:** 1.0  
**Date:** 2026-08-01  
**Status:** Active  
**Project:** Tekson Manufacturing MES  

---

## Overview

This checklist ensures consistent, safe deployments of MES to any environment (Development, UAT, Production).

**Usage:** Complete all items before and after each deployment.

---

## Pre-Deployment Checklist

### Code & Tests

- [ ] All unit tests passing (`bench run-tests`)
- [ ] All integration tests passing
- [ ] Code review completed
- [ ] No linting errors (`bench lint`)
- [ ] Test coverage >80%
- [ ] No console.log or debug statements
- [ ] All docstrings complete

### Database & Migrations

- [ ] `bench migrate` executed successfully
- [ ] All patches in `patches.txt` reviewed
- [ ] Custom fields created/updated
- [ ] Custom DocTypes created/updated
- [ ] Property Setters applied
- [ ] Database backup completed
- [ ] Migration rollback tested

### Assets & Build

- [ ] `bench build --app tekson_manufacturing` successful
- [ ] CSS/JS assets generated
- [ ] No build errors or warnings
- [ ] Assets cache cleared

### Configuration

- [ ] MES Settings configured
- [ ] All 40 configuration settings reviewed
- [ ] Environment variables set (if applicable)
- [ ] Hooks.py updated and tested
- [ ] Roles and permissions configured

### Documentation

- [ ] CHANGELOG.md updated
- [ ] KNOWN_LIMITATIONS.md updated (if applicable)
- [ ] TECHNICAL_DEBT.md updated (if applicable)
- [ ] Release notes prepared
- [ ] User documentation updated (if applicable)

---

## Deployment Execution

### Step 1: Pre-Deployment Backup

```bash
# Database backup
bench --site [site_name] backup

# Verify backup exists
ls -lh sites/[site_name]/private/backups/

# Backup files
cp -r sites/[site_name]/private/files/ /backup/files_backup_$(date +%Y%m%d)
```

- [ ] Database backup completed
- [ ] Files backup completed
- [ ] Backup verified (restore test)

---

### Step 2: Code Deployment

```bash
# Pull latest code
git pull origin develop

# Check current branch
git branch

# Verify commit hash
git log --oneline -1
```

- [ ] Code pulled successfully
- [ ] Correct branch checked out
- [ ] Commit hash verified

---

### Step 3: Migration Execution

```bash
# Run migrations
bench --site [site_name] migrate

# Check for errors
echo $?

# Verify patch execution
bench --site [site_name] execute "frappe.get_last_doc('Patch Log')"
```

- [ ] Migration completed without errors
- [ ] All patches executed
- [ ] No migration warnings

---

### Step 4: Asset Build

```bash
# Build assets
bench build --app tekson_manufacturing

# Clear cache
bench --site [site_name] clear-cache

# Clear Redis cache
bench --site [site_name] clear-redis-cache
```

- [ ] Assets built successfully
- [ ] Cache cleared
- [ ] No build errors

---

### Step 5: Post-Migration Verification

```bash
# Verify custom fields
bench --site [site_name] execute "print(frappe.get_all('Custom Field', {'module': 'Tekson Manufacturing'}, pluck='name'))"

# Verify custom DocTypes
bench --site [site_name] execute "print(frappe.get_all('DocType', {'module': 'Tekson Manufacturing'}, pluck='name'))"

# Check MES Settings
bench --site [site_name] execute "print(frappe.get_doc('MES Settings', 'MES Settings'))"
```

- [ ] Custom fields verified
- [ ] Custom DocTypes verified
- [ ] MES Settings accessible

---

## Post-Deployment Verification

### Smoke Tests

#### Core Functionality

- [ ] Work Order can be created
- [ ] Job Card can be created
- [ ] Stock Entry can be created
- [ ] Material Readiness evaluation works
- [ ] Dependency validation works
- [ ] Job Card start validation works
- [ ] Job Card completion validation works
- [ ] Work Order completion works

#### API Endpoints

- [ ] `evaluate_material_readiness()` responds
- [ ] `can_job_card_start()` responds
- [ ] `can_complete_job_card()` responds
- [ ] `complete_work_order_api()` responds
- [ ] `validate_previous_operation()` responds
- [ ] `validate_sequence()` responds

#### Integration Points

- [ ] Job Card → Work Order link works
- [ ] Stock Entry → Work Order link works
- [ ] Material Readiness → Execution integration works
- [ ] Dependency → Execution integration works

---

### Performance Checks

- [ ] Job Card open < 1 second
- [ ] Job Card start < 2 seconds
- [ ] Material Readiness evaluation < 3 seconds
- [ ] Work Order completion < 3 seconds
- [ ] No database timeouts
- [ ] No memory leaks

---

### Security Checks

- [ ] User permissions enforced
- [ ] Department scope enforced (if configured)
- [ ] No unauthorized access
- [ ] Session timeout working
- [ ] Action logging enabled

---

### Data Integrity

- [ ] No duplicate Stock Entries
- [ ] Job Card sequence intact
- [ ] Work Order status correct
- [ ] Stock balances accurate
- [ ] No orphaned records

---

## Rollback Procedure

### If Deployment Fails

#### Step 1: Stop Services

```bash
# Stop bench
bench stop
```

#### Step 2: Restore Database

```bash
# Restore from backup
bench --site [site_name] restore /path/to/backup.sql.gz
```

#### Step 3: Restore Code

```bash
# Checkout previous version
git checkout [previous_commit_hash]

# Pull stable version
git pull origin [stable_branch]
```

#### Step 4: Restore Files

```bash
# Restore backed up files
cp -r /backup/files_backup_YYYYMMDD/* sites/[site_name]/private/files/
```

#### Step 5: Restart Services

```bash
# Start bench
bench start
```

#### Step 6: Verify Rollback

- [ ] Database restored
- [ ] Code rolled back
- [ ] Files restored
- [ ] Application running
- [ ] Smoke tests passing

---

## Environment-Specific Checklists

### Development Environment

- [ ] Debug mode enabled
- [ ] Test data loaded
- [ ] Logging level: DEBUG
- [ ] Auto-reload enabled

### UAT Environment

- [ ] Debug mode disabled
- [ ] UAT test data loaded
- [ ] Logging level: INFO
- [ ] Performance monitoring enabled
- [ ] User access configured

### Production Environment

- [ ] Debug mode disabled
- [ ] Logging level: WARNING
- [ ] Performance monitoring enabled
- [ ] Backup schedule configured
- [ ] Monitoring alerts configured
- [ ] Rollback procedure tested
- [ ] Support team notified

---

## Sign-Off

### Deployment Team

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Technical Lead | | | |
| Developer | | | |
| QA Engineer | | | |
| System Administrator | | | |

### Business Sign-Off (Production Only)

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Production Manager | | | |
| Stores Manager | | | |
| Business Owner | | | |

---

## Deployment History

| Version | Date | Environment | Status | Deployed By |
|---------|------|-------------|--------|-------------|
| 1.0.4 | 2026-08-01 | Development | ✅ Success | Development Team |
| - | - | UAT | ⏳ Pending | - |
| - | - | Production | ⏳ Pending | - |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-08-01 | Development | Initial creation |

---

## Related Documents

- PHASE1_STATUS_REPORT.md - Project status
- CHANGELOG.md - Version history
- KNOWN_LIMITATIONS.md - Known issues
- MES_MIGRATION_STRATEGY.md - Migration approach
