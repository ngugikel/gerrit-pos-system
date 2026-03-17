# 🍷 Gerrit POS System

## ✅ NO FOLDERS VERSION - GitHub Web Upload Ready!

This version is specifically designed to work with **GitHub's web interface** which cannot upload folders.

All code is contained in a **single file**: `index.py`

---

## 🚀 DEPLOY IN 3 EASY STEPS

### Step 1: Upload to GitHub (No Commands Needed!)

1. Go to https://github.com and login
2. Click **"+"** (top right) → **"New repository"**
3. Name it: `gerrit-pos-system`
4. Check: ✅ "Add a README file"
5. Click **"Create repository"**
6. Click **"Add file"** → **"Upload files"**
7. **Drag and drop these 4 files** from this folder:
   - `index.py` (main application)
   - `requirements.txt` (dependencies)
   - `vercel.json` (configuration)
   - `.gitignore` (optional)
8. Click **"Commit changes"**

✅ **Done!** All files uploaded successfully.

---

### Step 2: Deploy to Vercel (1 Click!)

1. Go to https://vercel.com and login
2. Click **"Add New..."** → **"Project"**
3. Find `gerrit-pos-system` → Click **"Import"**
4. Framework Preset: Select **"Other"**
5. Click **"Deploy"**
6. Wait 1-2 minutes...
7. **🎉 Your POS is live!**

---

### Step 3: Access Your POS System

**Your URL will be:**
```
https://gerrit-pos-system.vercel.app
```

**Login with:**
- Username: `admin`
- Password: `padmin123`

**Change this password before using in production!**

---

## 📦 What's in This Package?

| File | Purpose | Size |
|------|---------|------|
| `index.py` | **Main application** (backend + frontend in one file) | ~57 KB |
| `requirements.txt` | Python dependencies | 2 lines |
| `vercel.json` | Vercel deployment config | 10 lines |
| `.gitignore` | Git ignore rules | 4 lines |
| `README.md` | This file | - |

**Total: Only 4 files to upload!**

---

## ✨ Features Included

- ✅ **Login System**: Secure authentication
- ✅ **220 Products**: Pre-loaded from your database
- ✅ **Dropdown Date Picker**: Last 30 days + next 7
- ✅ **Sales Tracking**: Shopping cart with real-time totals
- ✅ **Inventory Management**: Stock updates & restocking
- ✅ **Excel Downloads**: 3 report types (.xlsx)
- ✅ **Statistics Dashboard**: Sales analytics
- ✅ **Multi-Computer Access**: Cloud hosted
- ✅ **Responsive Design**: Works on mobile & desktop

---

## 🔐 Security

**Default Credentials:**
```
Username: admin
Password: padmin123
```

**To change password:**
1. Open `index.py` in any text editor
2. Find: `ADMIN_USERNAME = 'admin'`
3. Find: `ADMIN_PASSWORD = 'padmin123'`
4. Change to your own
5. Save and re-upload to GitHub
6. Vercel will auto-redeploy!

---

## 📊 Excel Reports

In the **Reports** tab, you can download:

1. **Sales Report** - All sales transactions
2. **Inventory Report** - Current stock levels
3. **Full Report** - Complete transaction history

All files are `.xlsx` format (Excel, Google Sheets compatible).

---

## 🛠️ How It Works

This is a **single-file Flask application** that:
- Serves the HTML/CSS/JS frontend
- Handles API requests for sales/inventory
- Manages user sessions
- Generates Excel reports

All embedded in one Python file for easy deployment!

---

## 🆘 Troubleshooting

### "Build Failed" on Vercel?
- Make sure `requirements.txt` was uploaded
- Check that `vercel.json` is valid JSON
- Verify `index.py` is in the root (not in a folder)

### "Page Not Found" errors?
- Check `vercel.json` routes configuration
- Ensure all 4 files are in the repository root

### Login not working?
- Check caps lock
- Try default: admin / padmin123
- Clear browser cookies

### Changes not showing?
- Hard refresh: `Ctrl+Shift+R`
- Check Vercel deployment status
- Verify GitHub file was updated

---

## 🔄 Making Updates

### To update your code:

**Option 1: GitHub Web (Easiest)**
1. Go to your repo on GitHub
2. Click on `index.py`
3. Click ✏️ (Edit button)
4. Make changes
5. Click "Commit changes"
6. Vercel auto-redeploys in 30 seconds!

**Option 2: Local Edit + Upload**
1. Edit `index.py` on your computer
2. Go to GitHub repo
3. Click "Add file" → "Upload files"
4. Drag updated `index.py`
5. Click "Commit changes"

---

## 🌐 Accessing from Different Computers

Once deployed, your team can access via:
```
https://gerrit-pos-system.vercel.app
```

- Works on any device (computer, phone, tablet)
- No installation required
- Real-time data sync
- Secure HTTPS connection

---

## 📞 Support

- **GitHub Docs**: https://docs.github.com
- **Vercel Docs**: https://vercel.com/docs
- **Flask Docs**: https://flask.palletsprojects.com

---

## 🎉 You're All Set!

Your POS system is ready to deploy. Just upload the 4 files to GitHub and deploy to Vercel!

**Questions?** Check the troubleshooting section above.

**Made with ❤️ for Gerrit**
