# -*- coding: utf-8 -*-
"""
الكودرهن - الحسابات والمصروفات
نسخة Python/Kivy تعمل محلياً باستخدام SQLite.
قاعدة الإجمالي: إجمالي الوارد + إجمالي المصروف (لا يتم الخصم).
"""
import os, sqlite3, json, datetime
from kivy.app import App
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.colorpicker import ColorPicker
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    def ar(s):
        try: return get_display(arabic_reshaper.reshape(str(s)))
        except Exception: return str(s)
except Exception:
    def ar(s): return str(s)

APP_NAME = "الكودرهن"
PALETTES = {
    "أحمر": {"primary":[0.71,0.10,0.10,1], "dark":[0.55,0.08,0.08,1], "accent":[0.08,0.35,0.23,1], "bg":[0.95,0.97,0.96,1], "card":[1,1,1,1], "text":[0.08,0.13,0.10,1]},
    "أخضر": {"primary":[0.08,0.39,0.25,1], "dark":[0.04,0.25,0.16,1], "accent":[0.72,0.30,0.07,1], "bg":[0.94,0.97,0.94,1], "card":[1,1,1,1], "text":[0.08,0.13,0.10,1]},
    "أزرق": {"primary":[0.10,0.29,0.62,1], "dark":[0.06,0.19,0.42,1], "accent":[0.82,0.40,0.08,1], "bg":[0.94,0.96,0.99,1], "card":[1,1,1,1], "text":[0.08,0.12,0.20,1]},
    "بنفسجي": {"primary":[0.39,0.16,0.60,1], "dark":[0.26,0.10,0.42,1], "accent":[0.78,0.30,0.40,1], "bg":[0.97,0.95,0.99,1], "card":[1,1,1,1], "text":[0.12,0.08,0.16,1]},
    "تركوازي": {"primary":[0.04,0.40,0.47,1], "dark":[0.02,0.26,0.31,1], "accent":[0.75,0.35,0.08,1], "bg":[0.93,0.97,0.97,1], "card":[1,1,1,1], "text":[0.06,0.14,0.15,1]},
    "برتقالي": {"primary":[0.78,0.31,0.06,1], "dark":[0.55,0.20,0.03,1], "accent":[0.08,0.36,0.25,1], "bg":[0.99,0.96,0.92,1], "card":[1,1,1,1], "text":[0.16,0.10,0.06,1]},
    "داكن": {"primary":[0.15,0.19,0.24,1], "dark":[0.08,0.11,0.15,1], "accent":[0.10,0.48,0.33,1], "bg":[0.91,0.93,0.94,1], "card":[1,1,1,1], "text":[0.06,0.08,0.10,1]},
}

class KodrhanApp(App):
    def build(self):
        self.title = APP_NAME
        self.db_path = os.path.join(self.user_data_dir, "kodrhan.db")
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.setup_db()
        self.settings = self.get_settings()
        self.palette = self.load_palette()
        Window.clearcolor = self.palette["bg"]
        self.root_box = BoxLayout(orientation="vertical", spacing=dp(6), padding=dp(8))
        self.header = Label(text=ar("الكودرهن\\nالحسابات والمصروفات"), size_hint_y=None, height=dp(66),
                            font_size="22sp", bold=True, color=[1,1,1,1])
        self.header.canvas.before.clear()
        self.header.canvas.before.clear()
        with self.header.canvas.before:
            Color(*self.palette["primary"])
            self.header_bg = RoundedRectangle(pos=self.header.pos, size=self.header.size, radius=[dp(16)])
        self.header.bind(pos=self._update_header_bg, size=self._update_header_bg)
        self.root_box.add_widget(self.header)
        self.body = BoxLayout(orientation="vertical")
        self.root_box.add_widget(self.body)
        self.nav = GridLayout(cols=4, size_hint_y=None, height=dp(54), spacing=dp(5))
        for label, fn in [("الرئيسية", self.show_home), ("السجل", self.show_ledger),
                          ("الأقسام", self.show_categories), ("الإعدادات", self.show_settings)]:
            self.nav.add_widget(self.make_button(label, fn, small=True))
        self.root_box.add_widget(self.nav)
        self.show_home()
        return self.root_box

    def _update_header_bg(self, *_):
        self.header_bg.pos = self.header.pos
        self.header_bg.size = self.header.size

    def setup_db(self):
        c=self.conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY AUTOINCREMENT, number TEXT UNIQUE NOT NULL, kind TEXT NOT NULL, category TEXT NOT NULL, amount REAL NOT NULL, date TEXT NOT NULL, person TEXT DEFAULT '', notes TEXT DEFAULT '')")
        c.execute("CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, kind TEXT NOT NULL)")
        c.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
        c.execute("INSERT OR IGNORE INTO categories(name,kind) VALUES('الكودرهن','in')")
        c.execute("INSERT OR IGNORE INTO categories(name,kind) VALUES('مصروفات خاصة','out')")
        c.execute("INSERT OR IGNORE INTO settings(key,value) VALUES('currency','جنيه')")
        c.execute("INSERT OR IGNORE INTO settings(key,value) VALUES('palette','أحمر')")
        c.execute("INSERT OR IGNORE INTO settings(key,value) VALUES('custom_palette','')")
        self.conn.commit()

    def get_settings(self):
        return {r["key"]:r["value"] for r in self.conn.execute("SELECT key,value FROM settings")}

    def set_setting(self,k,v):
        self.conn.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)",(k,str(v)))
        self.conn.commit()
        self.settings=self.get_settings()

    def load_palette(self):
        custom=self.settings.get("custom_palette","")
        if custom:
            try: return json.loads(custom)
            except: pass
        return PALETTES.get(self.settings.get("palette","أحمر"), PALETTES["أحمر"])

    def apply_palette(self):
        self.palette=self.load_palette()
        Window.clearcolor=self.palette["bg"]
        self.header.canvas.before.clear()
        with self.header.canvas.before:
            Color(*self.palette["primary"])
            self.header_bg=RoundedRectangle(pos=self.header.pos,size=self.header.size,radius=[dp(16)])
        self.header.color=[1,1,1,1]
        self.refresh_current()

    def make_label(self, text, size=16, color=None, bold=False, height=None):
        w=Label(text=ar(text), font_size=f"{size}sp", color=color or self.palette["text"],
                bold=bold, halign="right", valign="middle", size_hint_y=None if height else 1,
                height=dp(height) if height else 1)
        w.bind(size=lambda inst,val: setattr(inst,"text_size",(max(0,val[0]-dp(12)),None)))
        return w

    def make_button(self, text, callback, primary=False, small=False):
        b=Button(text=ar(text), size_hint_y=None, height=dp(42 if small else 48),
                 font_size="13sp" if small else "15sp", bold=True,
                 background_normal="", background_down="",
                 background_color=self.palette["primary"] if primary else [0.90,0.94,0.92,1],
                 color=[1,1,1,1] if primary else self.palette["text"])
        b.bind(on_release=lambda *_:callback())
        return b

    def clear_body(self):
        self.body.clear_widgets()

    def page_title(self, title):
        self.body.add_widget(self.make_label(title, size=20, bold=True, height=42))

    def card(self, content, height=None):
        box=BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(6),
                      size_hint_y=None if height else 1, height=dp(height) if height else 1)
        with box.canvas.before:
            Color(*self.palette["card"])
            bg=RoundedRectangle(pos=box.pos,size=box.size,radius=[dp(16)])
        box.bind(pos=lambda i,v:setattr(bg,"pos",v),size=lambda i,v:setattr(bg,"size",v))
        for w in content: box.add_widget(w)
        return box

    def totals(self):
        incoming=self.conn.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE kind='in'").fetchone()[0]
        outgoing=self.conn.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE kind='out'").fetchone()[0]
        # حسب طلب المستخدم: المصروف يضاف إلى الوارد في الإجمالي الكلي ولا يخصم منه.
        grand=float(incoming)+float(outgoing)
        return float(incoming),float(outgoing),grand

    def fmt(self,n):
        return f"{n:,.2f}".rstrip("0").rstrip(".") + " " + self.settings.get("currency","جنيه")

    def show_home(self):
        self.current_page="home"; self.clear_body()
        scroll=ScrollView()
        content=BoxLayout(orientation="vertical",spacing=dp(10),size_hint_y=None,padding=[0,0,0,dp(10)])
        content.bind(minimum_height=content.setter("height"))
        inc,out,grand=self.totals()
        hero=BoxLayout(orientation="vertical",padding=dp(14),spacing=dp(7),size_hint_y=None,height=dp(192))
        with hero.canvas.before:
            Color(*self.palette["primary"]); bg=RoundedRectangle(pos=hero.pos,size=hero.size,radius=[dp(18)])
        hero.bind(pos=lambda i,v:setattr(bg,"pos",v),size=lambda i,v:setattr(bg,"size",v))
        hero.add_widget(self.make_label("الإجمالي الكلي (الوارد + المصروف)",15,[1,1,1,1],True,28))
        hero.add_widget(self.make_label(self.fmt(grand),31,[1,1,1,1],True,55))
        row=GridLayout(cols=2,spacing=dp(7),size_hint_y=None,height=dp(75))
        row.add_widget(self.make_label("إجمالي الوارد\\n"+self.fmt(inc),15,[1,1,1,1],True,70))
        row.add_widget(self.make_label("إجمالي المصروف\\n"+self.fmt(out),15,[1,1,1,1],True,70))
        hero.add_widget(row); content.add_widget(hero)
        content.add_widget(self.make_label("الأقسام",19,bold=True,height=35))
        cats=self.conn.execute("SELECT name,kind FROM categories ORDER BY id").fetchall()
        for c in cats:
            total=self.conn.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE category=?",(c["name"],)).fetchone()[0]
            typ="وارد" if c["kind"]=="in" else "منصرف"
            content.add_widget(self.card([self.make_label(f"{c['name']} — {typ}",16,bold=True,height=28),
                                          self.make_label(self.fmt(total),22,self.palette["accent"],True,36)],height=86))
        content.add_widget(self.make_label("آخر العمليات",19,bold=True,height=35))
        rows=self.conn.execute("SELECT * FROM transactions ORDER BY id DESC LIMIT 6").fetchall()
        if not rows: content.add_widget(self.make_label("لا توجد عمليات مسجلة",14,self.palette["text"],False,45))
        for r in rows: content.add_widget(self.tx_row(r))
        scroll.add_widget(content); self.body.add_widget(scroll)

    def tx_row(self,r):
        box=BoxLayout(orientation="horizontal",size_hint_y=None,height=dp(66),spacing=dp(6),padding=dp(6))
        with box.canvas.before:
            Color(*self.palette["card"]); bg=RoundedRectangle(pos=box.pos,size=box.size,radius=[dp(12)])
        box.bind(pos=lambda i,v:setattr(bg,"pos",v),size=lambda i,v:setattr(bg,"size",v))
        title=f"{r['number']} | {r['category']}\\n{r['date']}  {r['person']}"
        box.add_widget(self.make_label(title,13,height=52))
        sign="+" if r["kind"]=="in" else "−"
        box.add_widget(self.make_label(sign+self.fmt(r["amount"]),14,self.palette["accent"],True,52))
        box.add_widget(self.make_button("تعديل",lambda rid=r["id"]:self.edit_transaction(rid),small=True))
        return box

    def show_ledger(self):
        self.current_page="ledger"; self.clear_body()
        self.page_title("سجل العمليات")
        bar=BoxLayout(size_hint_y=None,height=dp(46),spacing=dp(6))
        self.search=TextInput(hint_text="بحث برقم العملية أو الاسم",multiline=False)
        self.search.bind(text=lambda *_:self.render_ledger_list())
        bar.add_widget(self.search); bar.add_widget(self.make_button("+ عملية",self.add_transaction,primary=True))
        self.body.add_widget(bar)
        self.ledger_list=BoxLayout(orientation="vertical",spacing=dp(6),size_hint_y=None)
        self.ledger_list.bind(minimum_height=self.ledger_list.setter("height"))
        scroll=ScrollView(); scroll.add_widget(self.ledger_list); self.body.add_widget(scroll)
        self.render_ledger_list()

    def render_ledger_list(self):
        if not hasattr(self,"ledger_list"): return
        self.ledger_list.clear_widgets()
        q=getattr(self,"search",None).text.strip().lower() if getattr(self,"search",None) else ""
        rows=self.conn.execute("SELECT * FROM transactions ORDER BY id DESC").fetchall()
        found=[r for r in rows if not q or q in (r["number"]+" "+r["person"]+" "+r["category"]+" "+r["notes"]).lower()]
        if not found: self.ledger_list.add_widget(self.make_label("لا توجد نتائج",14,height=50))
        for r in found: self.ledger_list.add_widget(self.tx_row(r))

    def show_categories(self):
        self.current_page="categories"; self.clear_body()
        self.page_title("الأقسام ومهامها")
        self.body.add_widget(self.make_button("+ إضافة قسم",self.add_category,primary=True))
        rows=self.conn.execute("SELECT * FROM categories ORDER BY id").fetchall()
        for r in rows:
            line=BoxLayout(size_hint_y=None,height=dp(52),spacing=dp(5))
            line.add_widget(self.make_label(r["name"]+" — "+("وارد" if r["kind"]=="in" else "منصرف"),14))
            line.add_widget(self.make_button("تعديل",lambda rid=r["id"]:self.rename_category(rid),small=True))
            self.body.add_widget(line)

    def show_settings(self):
        self.current_page="settings"; self.clear_body()
        scroll=ScrollView(); content=BoxLayout(orientation="vertical",spacing=dp(8),size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))
        content.add_widget(self.make_label("الإعدادات والمظهر",20,bold=True,height=42))
        content.add_widget(self.make_label("اختر لون التطبيق",16,bold=True,height=30))
        for name in PALETTES:
            p=PALETTES[name]
            b=Button(text=ar(name),size_hint_y=None,height=dp(42),background_normal="",background_color=p["primary"],color=[1,1,1,1],bold=True)
            b.bind(on_release=lambda _,n=name:self.choose_palette(n))
            content.add_widget(b)
        content.add_widget(self.make_label("لون مخصص",16,bold=True,height=32))
        content.add_widget(self.make_button("اختيار أي لون من عجلة الألوان",self.custom_color))
        content.add_widget(self.make_label("العملة",16,bold=True,height=28))
        self.currency_input=TextInput(text=self.settings.get("currency","جنيه"),multiline=False,size_hint_y=None,height=dp(44))
        content.add_widget(self.currency_input)
        content.add_widget(self.make_button("حفظ العملة",self.save_currency,primary=True))
        content.add_widget(self.make_label("البيانات محفوظة محلياً على الجهاز باستخدام قاعدة SQLite، ولا تحتاج إلى الإنترنت.",13,height=58))
        content.add_widget(self.make_button("تصدير نسخة احتياطية JSON",self.export_backup))
        content.add_widget(self.make_button("استيراد نسخة احتياطية JSON",self.import_backup))
        scroll.add_widget(content); self.body.add_widget(scroll)

    def refresh_current(self):
        page=getattr(self,"current_page","home")
        {"home":self.show_home,"ledger":self.show_ledger,"categories":self.show_categories,"settings":self.show_settings}.get(page,self.show_home)()

    def add_transaction(self):
        self.transaction_popup()

    def transaction_popup(self, record=None):
        edit=record is not None
        box=BoxLayout(orientation="vertical",spacing=dp(7),padding=dp(10))
        kind=Spinner(text=("وارد" if not edit or record["kind"]=="in" else "منصرف"),values=("وارد","منصرف"),size_hint_y=None,height=dp(42))
        cats=self.conn.execute("SELECT name FROM categories WHERE kind=?",( "in" if kind.text=="وارد" else "out",)).fetchall()
        cat=Spinner(text=(record["category"] if edit else (cats[0]["name"] if cats else "")),values=tuple(x["name"] for x in cats),size_hint_y=None,height=dp(42))
        number=TextInput(hint_text="رقم العملية (إجباري)",text=record["number"] if edit else "",multiline=False,size_hint_y=None,height=dp(42))
        amount=TextInput(hint_text="المبلغ",text=str(record["amount"]) if edit else "",input_filter="float",multiline=False,size_hint_y=None,height=dp(42))
        date=TextInput(hint_text="التاريخ YYYY-MM-DD",text=record["date"] if edit else datetime.date.today().isoformat(),multiline=False,size_hint_y=None,height=dp(42))
        person=TextInput(hint_text="اسم الشخص / الجهة (اختياري)",text=record["person"] if edit else "",multiline=False,size_hint_y=None,height=dp(42))
        notes=TextInput(hint_text="البيان والملاحظات",text=record["notes"] if edit else "",size_hint_y=None,height=dp(72))
        def update_cats(*_):
            vals=tuple(x["name"] for x in self.conn.execute("SELECT name FROM categories WHERE kind=?",("in" if kind.text=="وارد" else "out",)).fetchall())
            cat.values=vals
            if vals and cat.text not in vals: cat.text=vals[0]
        kind.bind(text=update_cats)
        for w in [kind,cat,number,amount,date,person,notes]: box.add_widget(w)
        alert=Label(text="",color=[0.85,0.05,0.05,1],size_hint_y=None,height=dp(28))
        box.add_widget(alert)
        buttons=GridLayout(cols=2,size_hint_y=None,height=dp(44),spacing=dp(6))
        pop=Popup(title=ar("تعديل عملية" if edit else "إضافة عملية"),content=box,size_hint=(.94,.88))
        def save(*_):
            num=number.text.strip()
            if not num or not amount.text.strip():
                alert.text=ar("أدخل رقم العملية والمبلغ أولاً"); return
            try: val=float(amount.text)
            except: alert.text=ar("المبلغ غير صحيح"); return
            if val<=0: alert.text=ar("يجب أن يكون المبلغ أكبر من صفر"); return
            duplicate=self.conn.execute("SELECT id FROM transactions WHERE lower(trim(number))=lower(trim(?)) AND id<>?",(num,record["id"] if edit else -1)).fetchone()
            if duplicate:
                alert.text=ar("تحذير: رقم العملية مدخل مسبقاً! أدخل رقماً جديداً."); return
            k="in" if kind.text=="وارد" else "out"
            if edit:
                self.conn.execute("UPDATE transactions SET number=?,kind=?,category=?,amount=?,date=?,person=?,notes=? WHERE id=?",
                                  (num,k,cat.text,val,date.text.strip() or datetime.date.today().isoformat(),person.text,notes.text,record["id"]))
            else:
                self.conn.execute("INSERT INTO transactions(number,kind,category,amount,date,person,notes) VALUES(?,?,?,?,?,?,?)",
                                  (num,k,cat.text,val,date.text.strip() or datetime.date.today().isoformat(),person.text,notes.text))
            self.conn.commit(); pop.dismiss(); self.refresh_current()
        buttons.add_widget(self.make_button("إلغاء",pop.dismiss))
        buttons.add_widget(self.make_button("حفظ العملية",save,primary=True))
        box.add_widget(buttons); pop.open()

    def edit_transaction(self, rid):
        r=self.conn.execute("SELECT * FROM transactions WHERE id=?",(rid,)).fetchone()
        if not r:return
        # عرض نافذة تعديل مع زر حذف منفصل
        self.transaction_popup(r)

    def add_category(self):
        box=BoxLayout(orientation="vertical",spacing=dp(8),padding=dp(10))
        name=TextInput(hint_text="اسم القسم",multiline=False,size_hint_y=None,height=dp(44))
        kind=Spinner(text="وارد",values=("وارد","منصرف"),size_hint_y=None,height=dp(44))
        msg=Label(text="",color=[.8,0,0,1],size_hint_y=None,height=dp(28))
        box.add_widget(name);box.add_widget(kind);box.add_widget(msg)
        pop=Popup(title=ar("إضافة قسم جديد"),content=box,size_hint=(.88,.42))
        def save(*_):
            n=name.text.strip()
            if not n: msg.text=ar("اكتب اسم القسم");return
            try:
                self.conn.execute("INSERT INTO categories(name,kind) VALUES(?,?)",(n,"in" if kind.text=="وارد" else "out"));self.conn.commit()
                pop.dismiss();self.show_categories()
            except sqlite3.IntegrityError: msg.text=ar("اسم القسم موجود مسبقاً")
        box.add_widget(self.make_button("حفظ القسم",save,primary=True));pop.open()

    def rename_category(self,rid):
        row=self.conn.execute("SELECT * FROM categories WHERE id=?",(rid,)).fetchone()
        if not row:return
        box=BoxLayout(orientation="vertical",spacing=dp(8),padding=dp(10))
        name=TextInput(text=row["name"],multiline=False,size_hint_y=None,height=dp(44));box.add_widget(name)
        pop=Popup(title=ar("تعديل اسم القسم"),content=box,size_hint=(.88,.3))
        def save(*_):
            n=name.text.strip()
            if n:
                self.conn.execute("UPDATE categories SET name=? WHERE id=?",(n,rid))
                self.conn.execute("UPDATE transactions SET category=? WHERE category=?",(n,row["name"]))
                self.conn.commit();pop.dismiss();self.show_categories()
        box.add_widget(self.make_button("حفظ",save,primary=True));pop.open()

    def choose_palette(self,name):
        self.set_setting("palette",name);self.set_setting("custom_palette","");self.apply_palette()

    def custom_color(self):
        picker=ColorPicker()
        pop=Popup(title=ar("اختر لون التطبيق المخصص"),content=picker,size_hint=(.95,.85))
        def apply(*_):
            chosen=list(picker.color)
            p=dict(self.palette);p["primary"]=chosen
            # اشتقاق لون داكن متناسق من اللون المختار
            p["dark"]=[max(0,c*.72) for c in chosen[:3]]+[1]
            self.set_setting("custom_palette",json.dumps(p));pop.dismiss();self.apply_palette()
        wrapper=BoxLayout(orientation="vertical")
        wrapper.add_widget(picker);wrapper.add_widget(self.make_button("اعتماد اللون",apply,primary=True))
        pop.content=wrapper;pop.open()

    def save_currency(self):
        self.set_setting("currency",self.currency_input.text.strip() or "جنيه")
        self.show_settings()

    def export_backup(self):
        data={"settings":self.get_settings(),"categories":[dict(r) for r in self.conn.execute("SELECT * FROM categories")],
              "transactions":[dict(r) for r in self.conn.execute("SELECT * FROM transactions")]}
        path=os.path.join(self.user_data_dir,"kodrhan-backup.json")
        with open(path,"w",encoding="utf-8") as f:json.dump(data,f,ensure_ascii=False,indent=2)
        self.message("تم إنشاء النسخة الاحتياطية داخل مجلد بيانات التطبيق:\\n"+path)

    def import_backup(self):
        self.message("لاستيراد نسخة JSON، انسخ الملف إلى مجلد بيانات التطبيق باسم kodrhan-import.json ثم أعد تشغيل التطبيق. سيتم إضافة واجهة اختيار الملفات في مرحلة التغليف النهائية.")

    def message(self,text):
        Popup(title=ar("الكودرهن"),content=Label(text=ar(text)),size_hint=(.9,.35)).open()

    def on_stop(self):
        try:self.conn.close()
        except:pass

if __name__ == "__main__":
    KodrhanApp().run()
