'use strict';
// Derive the online UI from the audited pilot; do not rewrite the offline source.
const fs=require('node:fs'),path=require('node:path');
let html=fs.readFileSync(path.join(__dirname,'index.html'),'utf8');
const edits=[
  [
    "פיילוט 0.1",
    "פיילוט 0.2"
  ],
  [
    "maxlength=\"8\"",
    "maxlength=\"12\""
  ],
  [
    "/^[0-9a-f]{8}$/i",
    "/^[0-9a-f]{12}$/i"
  ],
  [
    "שמונה תווים",
    "12 תווים"
  ],
  [
    "בלי מעקב",
    "בלי אנליטיקה במשחק"
  ],
  [
    "חדר מקוון עובד בין מכשירים המחוברים לאותו שרת פיילוט.",
    "שלחו לחבר את קישור החדר. כל זוג משחק בחדר נפרד."
  ],
  [
    "function setState(s){",
    "function setState(s){if(!local&&s.code===room?.code&&s.revision<room.revision)return;"
  ],
  [
    "stream.addEventListener('expired',()=>",
    "stream.addEventListener('restarting',()=>{stream.close();room=null;history.replaceState(null,'',location.pathname);lobbyScreen();notify('שרת הפיילוט הופעל מחדש. יש לפתוח חדר חדש; התוצאה הקודמת לא נשמרה.');});stream.addEventListener('expired',()=>"
  ],
  [
    "חדר השרת פג לאחר 30 דקות ללא פעולה או אחרי שעתיים לכל היותר. סגירת לשונית אינה מוחקת את החדר מיד.",
    "חדר השרת פג לאחר 30 דקות ללא פעולה או אחרי שעתיים לכל היותר. סגירת לשונית אינה מוחקת את החדר מיד. הפעלה מחדש של שרת הפיילוט מוחקת חדרים. שירות האירוח עשוי לעבד נתוני רשת טכניים; המשחק אינו רושם אותם."
  ]
];
for(const [from,to] of edits){if(!html.includes(from))throw new Error('Online UI source anchor missing');html=html.split(from).join(to);}
fs.writeFileSync(path.join(__dirname,'online.html'),html);
console.log('Built online.html; no server answers or offline engine embedded.');
