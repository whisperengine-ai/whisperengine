# External Chat API Security Configuration

## CORS (Cross-Origin Resource Sharing)

The External Chat API implements environment-controlled CORS to protect against unauthorized access.

### Configuration

Set the `ALLOWED_ORIGINS` environment variable with a comma-separated list of allowed origins:

```bash
# Development (default if not set)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# Production example
ALLOWED_ORIGINS=https://app.example.com,https://dashboard.example.com
```

### Behavior

- **Allowed Origins**: Requests from configured origins will include proper CORS headers
- **Unauthorized Origins**: Requests from other origins will be rejected (no CORS headers)
- **Security Logging**: Rejected origins are logged for security monitoring
- **Preflight Requests**: OPTIONS requests are handled automatically

### Testing CORS

```bash
# Test allowed origin
curl -H "Origin: http://localhost:3000" http://localhost:8080/api/health

# Test unauthorized origin (should be rejected)
curl -H "Origin: http://unauthorized.com" http://localhost:8080/api/health
```

### Security Best Practices

1. **Never use wildcard (`*`)** for production APIs
2. **Only include trusted domains** in ALLOWED_ORIGINS
3. **Use HTTPS origins** in production
4. **Monitor logs** for unauthorized access attempts
5. **Keep the list minimal** - only include necessary origins

## Rate Limiting (Future Enhancement)

Rate limiting is not currently implemented but should be added before production deployment:

- Per-IP rate limiting
- Per-user rate limiting (if authentication is implemented)
- Burst protection for batch endpoints

## Authentication (Future Enhancement)

Consider adding authentication for production use:

- API key authentication
- JWT tokens
- OAuth 2.0 for external applications
