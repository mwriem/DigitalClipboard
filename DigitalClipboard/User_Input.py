import sys, datetime, os, subprocess, ctypes
from time import sleep
from tkinter import *
from tkinter import messagebox
import tkinter as tk
from tkinter.ttk import *
import tkinter.ttk as ttk
import tkinter.font as tkFont
from Datastore import Datastore
from LogEvent import LogEvent
from Signature_Input import Signature_Input
from DeviceMaps import DeviceMaps
from Common import Logger
from Common import LogTypeString as lts

class User_Input(object):
    """This will be the python user interface to gather check in/out info"""

    barcode = "-2"
    defaultbg = ""
    otherselected = False
    othervisible = False
    isintextbox = False
    isDestroyed = False

    def Checking_In(self):
        #Logger.Add("Checking_In Called", lts.GEN)

        # Check for null barcode
        if(self.barcode == "-2"):
            return
        # Create LogEvent obj
        logevent = LogEvent()

        # Update LogEvent obj
        logevent.Add_Barcode(self.barcode)
        logevent.Add_Status("--IN --")
        missing_entry = False

        # Get Current date and time
        date_time = datetime.datetime.now()
        logevent.Add_DateTime(date_time)

        # Get Name from text field
        txt = self.txtname.get()
        logevent.Add_Username(txt)
        if txt == "":
            self.txtname.config(highlightbackground="red", highlightcolor="red", highlightthickness=2)
            missing_entry = True

        # Get ECN from text field
        txtecn = self.txtecn.get()
        logevent.Add_ECN(txtecn)
        if txtecn == "":
            self.txtecn.config(highlightbackground="red", highlightcolor="red", highlightthickness=2)
            missing_entry = True

        # Get Tech from drop down
        txttech = self.optionvar.get()
        logevent.Add_Tech(txttech)
        if txttech == 'No Technician':
            self.txttech.configure(highlightbackground="red", highlightcolor="red")
            missing_entry = True

        # Get Reason
        txtreason = self.reasonoptionvar.get()
        if txtreason == '':
            self.txtreason.configure(highlightbackground="red", highlightcolor="red")
        # Get Notes if empty flag else add it to reason
        if txtreason == 'Other':
            txtreason = self.txtother.get()
            if txtreason == '':
                self.txtother.config(highlightbackground="red", highlightcolor="red", highlightthickness=2)
                missing_entry = True
        else:
            txtreason = "{0} : {1}".format(txtreason, self.txtother.get())

        logevent.Add_Comment(txtreason)

        # Missing entry highlight entry fields
        if missing_entry:
            return

        if self.Check_Device_Status() is True:
            answer = messagebox.askyesno("Question","This device has already been checked in, continue?")
            if not answer:
                return

        # Log the LogEvent to file
        Datastore().Add(logevent.Get_Log())
        
        # Save ecn, name, and barcode
        self.Save_JSON(txtecn, txt, True)

        self.root.destroy()
        return


    def Checking_Out(self):
        #Logger.Add("Checking_Out Called", lts.GEN)
        if(self.barcode == "-2"):
            return
        # Create LogEvent obj        
        logevent = LogEvent()
        
        # Update LogEvent obj
        logevent.Add_Barcode(self.barcode)
        logevent.Add_Status("--OUT--")

        missing_entry = False
        
        # Get Current date and time
        date_time = datetime.datetime.now()
        logevent.Add_DateTime(date_time)

        # Get Name from text field
        txt = self.txtname.get()
        logevent.Add_Username(txt)
        if txt == "":
            self.txtname.config(highlightbackground="red", highlightcolor="red", highlightthickness=2)
            missing_entry = True

        # Get ECN from text field
        txtecn = self.txtecn.get()
        logevent.Add_ECN(txtecn)
        if txtecn == "":
            self.txtecn.config(highlightbackground="red", highlightcolor="red", highlightthickness=2)
            missing_entry = True
            
        # Get Tech from drop down
        txttech = self.optionvar.get()
        logevent.Add_Tech(txttech)
        if txttech == 'No Technician':
            self.txttech.config(highlightbackground="red", highlightcolor="red")
            missing_entry = True

        # Get Reason from drop down
        txtreason = self.reasonoptionvar.get()
        if self.otherselected:
            txtreason = self.txtother.get()
        logevent.Add_Comment(txtreason)

        # Missing entry highlight entry fields
        if missing_entry:
            return

        if self.Check_Device_Status() is False:
            answer = messagebox.askyesno("Question","This device has already been checked out, continue?")
            if not answer:
                return

        if not hasattr(self, 'sig_input'):
            self.sig_input = Signature_Input(date_time, txtecn)
            logevent.Add_Signature(self.sig_input.GetFileName())

        # Log the LogEvent to file
        Datastore().Add(logevent.Get_Log())

        # Get Signature if all data is present
        self.Get_Signature()

        # Save ecn, name, and barcode
        self.Save_JSON(txtecn, txt, False)



    def Check_Device_Status(self):
        ecn = self.txtecn.get()
        if ecn in self.deviceMaps.keys():
            return self.deviceMaps[ecn]["CheckedIn"]
            

    def Save_JSON(self, ecn, name, checkedin):
        barcode = self.barcode
        self.deviceMapsClass.Add_mapping(ecn, barcode, name, checkedin)


    def Get_Signature(self):
        if self.sig_input.isOpen:
            self.Raise_Window()
        else:
            self.sig_input.Run(self.root)
    

    def on_focus_in(self, e):
            #Logger.Add('on_focus_in', lts.GEN)
            subprocess.Popen("osk", shell=True)


    def on_focus_out(self, e):
            if not self.isintextbox:
                #Logger.Add('on_focus_out', lts.GEN)
                subprocess.call('wmic process where name="osk.exe" delete', shell=True)


    def on_enter(self, e):
        # Hover over button
        e.widget['style'] = "HOV.TButton"


    def on_leave(self, e):
        # Leave Hover over button
        if e.widget is self.exit:
            e.widget['style'] = "BWR.TButton"
        else:
            e.widget['style'] = "BW.TButton"


    def t_on_enter(self, e):
        self.isintextbox = True


    def t_on_leave(self, e):
        self.isintextbox = False


    def __init__(self, barcode, root):
        Logger.Add("UI Start Called", lts.GEN)

        # GET Mapping Data
        self.deviceMapsClass = DeviceMaps()
        self.deviceMaps = self.deviceMapsClass.deviceMaps

        # Init Textbox Variables
        name = tk.StringVar()
        ecn = tk.StringVar()

        # Update Name and ECN
        for v in self.deviceMaps.values():
            if v['Barcode'] == barcode:
                name.set(v['Name'])
                ecn.set(v['ECN'])
                break

        # Styles / Sizing / Colors
        bg_color = 'white smoke'
        width_s = 30
        btn_width = 30
        txt_width = 30
        font_s = tkFont.Font(family="Courier", size=15)
        font_small = tkFont.Font(family="Courier", size=14)
        style_font = ('Courier', 16)
        self.style = ttk.Style()
        self.style.configure('.', foreground="black", background=bg_color, font=style_font)
        self.style.configure("BW.TLabel", width=width_s, anchor="e")
        self.style.configure("BW.TEntry", width=width_s)
        self.style.configure("ERROR.TEntry", width=width_s)
        self.style.configure("BW.TButton", height=2, width=width_s, relief=GROOVE)
        self.style.configure("BWR.TButton", background="black", height=2, width=width_s, relief=GROOVE)
        self.style.configure("HOV.TButton", background="white", height=2, width=width_s, relief=GROOVE)

        # UI barcode property
        self.barcode = barcode

        # Setup GUI
        self.root = root
        self.root.title = "Digital Clipboard"

        self.root.configure(bg=bg_color)
        self.root.state('zoomed')
        self.root.bind("<1>", self.on_focus_out)
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=2)
        self.root.columnconfigure(2, weight=3)
        self.root.columnconfigure(3, weight=1)

        # Header display for Barcode Data
        self.header = ttk.Label(root, text="Barcode:", style="BW.TLabel")
        self.header.grid(row=0, column=1, pady=(25,25), padx=(20,20), sticky=E)
        
        self.valheader = ttk.Label(root, text="{0}".format(barcode), style="BW.TLabel", anchor="w", font=font_small)
        self.valheader.grid(row=0, column=2, pady=(25,25), padx=(25,20), sticky=W)

        # Name Section
        self.lbluser = ttk.Label(root, text="Your Name:", style="BW.TLabel")
        self.lbluser.grid(row=1, column=1, pady=(10,25), padx=(20,20), sticky=E)
        
        self.txtname = tk.Entry(root, textvariable=name)
        self.txtname.configure(font=style_font, width=txt_width)
        self.txtname.bind("<1>", self.on_focus_in)
        self.txtname.bind("<Enter>", self.t_on_enter)
        self.txtname.bind("<Leave>", self.t_on_leave)
        self.txtname.grid(row=1, column=2, pady=(10,25), padx=(20,20), sticky=W)

        # ECN Section
        self.lblecn = ttk.Label(root, text="ECN:", style="BW.TLabel")
        self.lblecn.grid(row=2, column=1, pady=(10,25), padx=(20,20), sticky=E)
        
        self.txtecn = tk.Entry(root, textvariable=ecn)
        self.txtecn.configure(font=style_font, width=txt_width)
        self.txtecn.bind("<1>", self.on_focus_in)
        self.txtecn.bind("<Enter>", self.t_on_enter)
        self.txtecn.bind("<Leave>", self.t_on_leave)
        self.txtecn.grid(row=2, column=2, pady=(10,25), padx=(20,20), sticky=W)

        # Technician Section
        self.lbltech = ttk.Label(root, text="Technician:", style="BW.TLabel")
        self.lbltech.grid(row=3, column=1, pady=(10,25), padx=(20,20), sticky=E)

        # This is where you would ADD/REMOVE for the Technician Name Dropdown
        OPTIONS = ["No Technician", "Mike Delsanto", "Max Young", "Kim Tartarini", "Bill Finizia", "Dan Kemp", "Sal Rafique", "Eric Hansen", "Michael Weigel"]
        self.optionvar = StringVar(root)
        self.optionvar.set(OPTIONS[0])
        
        self.txttech = tk.OptionMenu(root, self.optionvar, *OPTIONS)
        self.txttech.configure(bg='white', font=font_s, width=btn_width)
        self.txttech.grid(row=3, column=2, pady=(10,25), padx=(20,20), sticky=W)
        self.txttech['menu'].config(font=font_s)

        # Reason Section
        self.lblreason = ttk.Label(root, text="Reason for visit:", style="BW.TLabel")
        self.lblreason.grid(row=4, column=1, pady=(10,25), padx=(20,20), sticky=E)
        
        # This is where you would ADD/REMOVE for the Reason Dropdown
        REASON_OPTIONS = ["New Device", "Replace Device", "Turn-In Device", "Hardware Issue/Install", "Software Issue/Install", "Checkout/Checkin Loaner", "Other"]
        self.reasonoptionvar = StringVar(root)
        self.txtreason = tk.OptionMenu(root, self.reasonoptionvar, *REASON_OPTIONS)
        self.txtreason.configure(bg='white', font=font_s, width=btn_width)
        self.txtreason.grid(row=4, column=2, pady=(10,25), padx=(20,20), sticky=W)
        self.txtreason['menu'].config(font=font_s)
        
        self.lblother = ttk.Label(root, text="Notes:", style="BW.TLabel")
        self.lblother.grid(row=5, column=1, pady=(5,25), padx=(20,20), sticky=E)

        self.txtother = tk.Entry(root,)
        self.txtother.configure(font=style_font, width=txt_width)
        self.txtother.bind("<1>", self.on_focus_in)
        self.txtother.bind("<Enter>", self.t_on_enter)
        self.txtother.bind("<Leave>", self.t_on_leave)
        self.txtother.grid(row=5, column=2, pady=(10,25), padx=(20,20), sticky=W)

        # Checkin Section
        self.checkin = ttk.Button(root, text="Checking In", command=self.Checking_In, style="BW.TButton")
        self.checkin.bind("<Enter>", self.on_enter)
        self.checkin.bind("<Leave>", self.on_leave)
        self.checkin.grid(row=6, column=2, pady=(10,25), padx=(20,20), columnspan=1, sticky=W)

        # Checkout Section
        self.checkout = ttk.Button(root, text="Checking Out", command=self.Checking_Out, style="BW.TButton")
        self.checkout.bind("<Enter>", self.on_enter)
        self.checkout.bind("<Leave>", self.on_leave)
        self.checkout.grid(row=7, column=2, pady=(10,25), padx=(20,20), columnspan=1, sticky=W)

        # Exit Section
        self.exit = ttk.Button(root, text="Close", command=self.Exit_Click, style="BWR.TButton")
        self.exit.bind("<Enter>", self.on_enter)
        self.exit.bind("<Leave>", self.on_leave)
        self.exit.grid(row=8, column=2, pady=(10,50), padx=(20,20), columnspan=1, sticky=W)

        self.root.mainloop()


    def Exit_Click(self):
        # Set isDestroyed so that the main digital clipboard loop exits after close button pressed.
        self.isDestroyed = True
        Logger.Add("Closing", lts.GEN)
        subprocess.call('wmic process where name="osk.exe" delete', shell=True)
        self.root.destroy()
        return


    def Raise_Window(self):
        self.sig_input.tk.lift()
        self.sig_input.tk.attributes("-topmost", True)
    

    def Change_Style(self, widget, theme):
        widget['style'] = theme