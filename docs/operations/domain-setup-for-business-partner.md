# Domain Setup Guide (Non-Technical)

**For**: Business Partner purchasing domain name
**Time**: 15-30 minutes
**Cost**: $12-15/year

---

## Step 1: Choose a Domain Name

Pick a domain name for the Churn Risk app. Examples:
- `churnrisk.com`
- `churn-risk.app`
- `yourcompany.com`

**Tips**:
- Keep it short and memorable
- Avoid hyphens if possible
- `.com` is most common, but `.app`, `.io`, `.co` work great too

---

## Step 2: Purchase the Domain

We recommend **Google Domains** for easiest integration:

### Using Google Domains (Recommended)

1. **Go to**: https://domains.google.com/

2. **Search** for your chosen domain name

3. **Add to cart** and proceed to checkout

4. **Fill out registration**:
   - Use company information
   - Privacy protection: **ON** (recommended)
   - Auto-renew: **ON** (recommended)

5. **Complete purchase** (~$12/year)

### Alternative: Cloudflare Registrar

1. **Go to**: https://www.cloudflare.com/products/registrar/

2. **Create free Cloudflare account** (if you don't have one)

3. **Search and purchase** domain (~$9-15/year)

**Note**: Cloudflare has excellent DNS management and is slightly cheaper

---

## Step 3: Configure DNS Settings

Once you've purchased the domain, you need to point it to our server.

### For Google Domains:

1. **Go to**: https://domains.google.com/registrar/

2. **Click** on your domain name

3. **Click** "DNS" in the left sidebar

4. **Scroll down** to "Custom records"

5. **Add two new records**:

   **Record 1:**
   - Host name: `@` (leave blank or use `@`)
   - Type: `A`
   - TTL: `1 hour`
   - Data: `136.110.172.10`
   - **Click "Add"**

   **Record 2:**
   - Host name: `www`
   - Type: `A`
   - TTL: `1 hour`
   - Data: `136.110.172.10`
   - **Click "Add"**

6. **Click "Save"**

### For Cloudflare:

1. **Go to**: Cloudflare Dashboard → Your Domain

2. **Click**: "DNS" tab

3. **Add two records**:

   **Record 1:**
   - Type: `A`
   - Name: `@`
   - IPv4 address: `136.110.172.10`
   - Proxy status: **Orange cloud OFF** (click to turn gray)
   - **Click "Save"**

   **Record 2:**
   - Type: `A`
   - Name: `www`
   - IPv4 address: `136.110.172.10`
   - Proxy status: **Orange cloud OFF** (click to turn gray)
   - **Click "Save"**

**IMPORTANT**: Make sure the orange cloud is **OFF** (gray). This is called "DNS only" mode.

---

## Step 4: Share Information with Technical Team

Once you've completed the setup, send this information:

```
✅ Domain purchased: [domain name here]
✅ DNS configured with:
   - A record: @ → 136.110.172.10
   - A record: www → 136.110.172.10
✅ Registrar: [Google Domains / Cloudflare / Other]
✅ Account access: [share login if needed]
```

---

## What Happens Next?

- **DNS propagation**: Takes 5 minutes to 48 hours (usually ~1 hour)
- **Technical team** will:
  - Set up HTTPS/SSL certificate (secure connection)
  - Configure the website to use the domain
  - Test everything is working

---

## Verification (Optional)

You can check if DNS is working by visiting:
- http://yourdomain.com (might show an error - this is OK for now)
- http://www.yourdomain.com (might show an error - this is OK for now)

If you see "This site can't be reached" with a DNS error, wait 30-60 minutes and try again.

---

## FAQ

**Q: Why can't I access the site yet?**
A: DNS takes time to propagate. The technical team also needs to configure SSL before it works with the domain.

**Q: What's the orange cloud in Cloudflare?**
A: That's Cloudflare's proxy. We need it **OFF** (gray) for initial setup.

**Q: Should I enable privacy protection?**
A: Yes! This hides your personal information from public WHOIS lookups.

**Q: What about email for this domain?**
A: That can be set up later separately (Google Workspace, etc.)

---

**Need Help?** Contact the technical team if you get stuck on any step.
