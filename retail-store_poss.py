import datetime
import sys
import csv
import random
from datetime import date
import mysql.connector

ref_userid =  'a' 
ref_password = 'a' 
i_count = 0

global cart, sale_return_register
cart = {}
sale_return_register = []

con = mysql.connector.connect(
                    user='admin', 
                    password='Possadmin0902', 
                    host='dbms-poss.c1ocramoglow.us-west-1.rds.amazonaws.com',
                    database='poss-dbms'
                    )

class Item:
    def __init__(self, UPC, Description, Item_Max_Qty, Order_Threshold, Replenishment_order_qty, Item_on_hand, Unit_price, Order_placed):
        self.UPC = UPC
        self.Description = Description
        self.Item_Max_Qty = Item_Max_Qty
        self.Order_Threshold = Order_Threshold
        self.Replenishment_order_qty = Replenishment_order_qty
        self.Item_on_hand = Item_on_hand
        self.Unit_Price = Unit_price
        self.Order_placed = Order_placed

class Store:
    items = {}
    def __init__(self):
        
        myCursor = con.cursor()
        sql = "SELECT UPC, Item_Description, Item_Max_Qty, Order_Threshold, replenishment_order_qty, Item_on_hand, Unit_price FROM RetailStoreItem"
        myCursor.execute(sql)
        myResult = myCursor.fetchall()

        for x in myResult:
            item = Item(x[0], x[1], x[2], x[3], x[4], x[5], x[6],0)
            # self.items.append(item)
            self.items[x[0]] = item

class SaleItem:
    def __init__(self, Reciept, UPC, Description, Qty, Unit_Price, TotalPrice, ReturnQty, Date):
        self.Reciept = Reciept
        self.UPC = UPC
        self.Description = Description
        self.Qty = Qty
        self.Unit_Price = Unit_Price
        self.TotalPrice = TotalPrice
        self.ReturnQty = ReturnQty
        self.Date = Date
       
class SaleDetails:
    sales = []
    def __init__(self, Reciept, UPC, Description, Qty, Unit_Price, TotalPrice, ReturnQty, Date, Trans_type):
        # if Trans_type == "Sale":
        saleItem = SaleItem(Reciept, UPC, Description, Qty, Unit_Price, TotalPrice, ReturnQty, Date)
        self.sales.append(saleItem)
        # if Trans_type == "Return"s

def replenish_order(upc):
    print("Order Replenishment.")
    if float(mystore.items[upc].Item_on_hand) <= float(mystore.items[upc].Order_Threshold):
        #create order file (orderid_upc_date # 78658765_12345_2021215.csv)
        file_name = "Order_" + str(random.randint(1, 10000)) + "_" + str(upc) + "_" + str(date.today()) + ".csv"
        order = 'UPC,Qunatity,Date\n'
        order = order + str(upc) + ',' + str(mystore.items[upc].Item_Max_Qty) + ',' + str(date.today())
        f = open(file_name, 'w')
        # create the csv writer
        writer = csv.writer(f)
        # write a row to the csv file
        writer.writerow([order])
        # close the file
        f.close()


def inventory_update(upc, qty, transaction):
    myCursor = con.cursor()
    if transaction == "sale":
        sql = "UPDATE RetailStoreItem SET Item_on_hand = Item_on_hand - " + qty + " WHERE UPC = " + upc
    if transaction == "return":
        sql = "UPDATE RetailStoreItem SET Item_on_hand = Item_on_hand + " + qty + " WHERE UPC = " + upc
    
    print(sql)
    myCursor.execute(sql)
    con.commit()


def sales_return_transaction(receipt_number, upc, qty, Unit_Price, total, return_qty, ref_userid):
    myCursor = con.cursor()
    sql = "INSERT INTO SalesReturnTransaction (RecieptID, UPC, QTY, Unit_Price, Total, Trans_datetime, Return_Qty, RepUserID) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    val = (receipt_number, upc, qty, Unit_Price, total, datetime.datetime.now(), return_qty, ref_userid)    
    print(sql)
    myCursor.execute(sql, val)
    con.commit()

def update_transaction(inp_num, inp_upc, inp_qty):
    myCursor = con.cursor()
    sql = "UPDATE SalesReturnTransaction SET Return_Qty = Return_Qty + " + inp_qty + " WHERE RecieptID = " + inp_num + " AND UPC = " + inp_upc 
    print(sql)
    myCursor.execute(sql)
    con.commit()

def return_items():
    print("Return Item/s.")
    
    # for i in SaleDetails.sales:
    #     print(i.Reciept,i.UPC,i.Description, i.Qty, i.Unit_Price,i.TotalPrice, i.ReturnQty, i.Date)
    #     total_sale = total_sale + float(i.TotalPrice)
    inp_num = input("\n\nPlease enter the reciept number: ")
    myCursor = con.cursor()
    sql = "SELECT RecieptID, UPC, QTY, Unit_Price, Total, Trans_datetime, Return_Qty, RepUserID FROM SalesReturnTransaction WHERE RecieptID = " + inp_num
    myCursor.execute(sql)
    myresult = myCursor.fetchall()

    #  validate if reciept is valid
    rexists = False

    for x in myresult:
        print(x[0])
        if inp_num == str(x[0]):
            rexists = True
    
    if rexists == False:
        print("Reciept doesn't exist.")
    else:
        inp_option = input("\n\n1. Return Single Item, 2. Return All Items: ")
        while True:
            if inp_option == "1":
                inp_upc = input("\n\nPlease enter UPC to be returned: ")
                for r in myresult:
                    print(r[0], " ", r[1])
                    if inp_num == str(r[0]) and inp_upc == str(r[1]):
                        inp_qty = input("\n\nPlease enter quantity: ")
                        if(int(inp_qty) > int(r[2]) - int(r[6])):
                            print("Item return quantity can't be more than sold quantity.")
                        else:
                            print("Returned Amount: ", float(inp_qty)*float(r[3]))
                            update_transaction(inp_num, inp_upc, inp_qty)
                            inventory_update(inp_upc,inp_qty,"return")
                        
            if inp_option == "2":
                inp_all = input("\n\n Are you sure you want to return all items? y = yes, n = No ")
                if inp_all == "y":
                    for r in myresult:
                        if inp_num == str(r[0]):
                            total_qty = int(r[2]) - int(r[6])
                            print("Returned Amount: ", float(total_qty)*float(r[3]))
                            inventory_update(inp_upc,total_qty,"return")
            
            poss_mgmt()




def complete_sale():

    total = 0.0
    # global sale
    reciet_number = random.randint(1, 1000000000)
    print("\n\nYour reciept number is: ", reciet_number)
    print("\n---------------------------------------------------------------------------------------\n")
    print("Product Description".ljust(30, " "), "Item Quantity".ljust(15, " "), "Price".ljust(10, " "), "Total".ljust(10, " "),"\n---------------------------------------------------------------------------------------\n")
    for upc,qty in cart.items():
        print(mystore.items[upc].Description.strip().ljust(30, " "), str(qty).ljust(15, " "), str(mystore.items[upc].Unit_Price).ljust(10, " "), "{:.2f}".format((float(mystore.items[upc].Unit_Price)*float(qty))))
        total = total + float(mystore.items[upc].Unit_Price)*float(qty)
        inventory_update(upc,qty,"sale")
        sales_return_transaction(reciet_number, upc, qty, mystore.items[upc].Unit_Price, total, 0, ref_userid)
        # obj = SaleDetails(reciet_number,upc,mystore.items[upc].Description.strip(),qty,mystore.items[upc].Unit_Price,float(mystore.items[upc].Unit_Price)*float(qty),0,'12/14/2021',"sale")
        # replenish_order(upc)
        # /sale_return_register.append(sale)
    cart.clear()


    print("\n---------------------------------------------------------------------------------------\nYour total amount is: ", round(total, 2),"\n---------------------------------------------------------------------------------------\n")
    poss_mgmt()

def new_sale():
    inp_upc_id = input("Please enter the UPC: ")
    print("You enterd: ", mystore.items[inp_upc_id].Description)

    inp_qty = input("Please enter quantity: ")
    print("The price is: ", "{:.2f}".format(float(mystore.items[inp_upc_id].Unit_Price) * float(inp_qty)))
    cart[inp_upc_id] = inp_qty

    while True:
        inp_option = input("\n\n1 = Sell another item, 2 = Return Item/s, 9 = Complete Sale: ")
        if inp_option == "1":
            new_sale()
        if inp_option == "2":
            return_items()
        if inp_option == "9":
            complete_sale()
            # cart.clear()
 


def backroom_operation():
    print("\n\nBackroom Operations.")
    int_num = input("\n1 = Create Orders for Replenishment, 2 = Print Inventory Report, 3 = Create Todays Item Sold Report, 9 = Back to home: ")
    
    while True:
        if int_num == "1":
            print("Order Replenishment.")
        if int_num == "2":
            print("\n---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------\nInventory Report\n---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------\n")
            print("UPC".ljust(15, " "),"PRODUCT".ljust(50, " "),"MAX QTY".ljust(20, " "),"THRESHOLD QTY".ljust(20, " "),"RPLNSMT QTY".ljust(20, " "),"ITEM ON HAND QTY".ljust(20, " "),"UNIT PRICE".ljust(10, " "),"ORDER PLACED QTY".ljust(20, " "))
            print("\n---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------\n")
            for i in mystore.items:
                print(mystore.items[i].UPC.ljust(15, " "), mystore.items[i].Description.strip().ljust(50, " "), mystore.items[i].Item_Max_Qty.ljust(20, " "), mystore.items[i].Order_Threshold.ljust(20, " ") , mystore.items[i].Replenishment_order_qty.ljust(20, " "), mystore.items[i].Item_on_hand.ljust(20, " "), mystore.items[i].Unit_Price.ljust(10, " "), mystore.items[i].Order_placed)
            print("\n---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------\n")
            poss_mgmt()

        if int_num == "3":
            total_sale = 0.00
            print("\n\n-------------------------------------------------------------------------------------------------------------------------\nTodays Item Sold Report.\n-------------------------------------------------------------------------------------------------------------------------\n")
            print("Reciept No".ljust(15, " "),"UPC".ljust(15, " "),"PRODUCT".ljust(30, " "),"QTY".ljust(10, " "),"UNIT PRICE".ljust(10, " "),"TOTAL SALE".ljust(10, " "),"ITEM RETURNED".ljust(10, " "),"DATE".ljust(10, " "))
            print("\n-------------------------------------------------------------------------------------------------------------------------\n")
            # print(sale_return_register.count())
            for i in SaleDetails.sales:
                print(str(i.Reciept).ljust(15, " "),str(i.UPC).ljust(15, " "),i.Description.strip().ljust(30, " "), str(i.Qty).ljust(10, " "), str(i.Unit_Price).ljust(10, " "),str(i.TotalPrice).ljust(10, " "), str(i.ReturnQty).ljust(10, " "), str(i.Date).ljust(10, " "))
                total_sale = total_sale + float(i.TotalPrice)
            print("\n\n-------------------------------------------------------------------------------------------------------------------------\nTotal Todays Sale: ",total_sale,"\n-------------------------------------------------------------------------------------------------------------------------\n")
            poss_mgmt()
        if int_num == "9":
            print("POSS System.")
            poss_mgmt()


def poss_mgmt():
    # Provide csv file full path or relative path to below code
    global mystore
    mystore = Store()
    # for i in mystore.items: 
    #     print(mystore.items[i].UPC.ljust(15, " "), mystore.items[i].Description.strip().ljust(50, " "), str(mystore.items[i].Item_Max_Qty).ljust(20, " "), str(mystore.items[i].Order_Threshold).ljust(20, " ") , str(mystore.items[i].Replenishment_order_qty).ljust(20, " "), str(mystore.items[i].Item_on_hand).ljust(20, " "), str(mystore.items[i].Unit_Price).ljust(10, " "), mystore.items[i].Order_placed)
    
    
    # int_num = input("\n\nPlease select your options \n1 = New Sale, 2 = Return Item/s, 3 = Backroom Operations, 9 = Exit Application: ")
    int_num = input("\n\nPlease select your options \n1 = New Sale, 2 = Return Item/s, 9 = Exit Application: ")
    while True:
        if int_num == "1":
            print("New Sale.")
            new_sale()
            break
        elif int_num == "2":
            return_items()
            break
        # elif int_num == "3":
        #     backroom_operation()
        #     break
        elif int_num == "9":
            print("Signed out from POSS system. Have a good day.")
            sys.exit()
            break
        else:
            print("Not a valid input, please enter correct input to operate.")
            poss_mgmt()
                

def user_login():    
    global i_count
    input_userid = input("Please enter userid: ")
    input_password = input("Please enter password: ")
    
    myCursor = con.cursor()
    sql = "SELECT UserName, UserPassword from UserDetails where UserName = '" + input_userid + "'"

    myCursor.execute(sql)
    myResult = myCursor.fetchone()

    mysql_userid = ''
    mysql_password = ''

    if myResult != None:
        mysql_userid = myResult[0]
        mysql_password = myResult[1]


    if input_userid == mysql_userid and input_password == mysql_password:
        poss_mgmt()

    else:
        i_count = i_count + 1
        if i_count >= 3:
            print(input_userid, " Your Account has been locked out. Please contact your system admin.")
        else:
            print("UserID and Password doesn't match, please try again. \n")
            user_login()


def main():
    print("\n\nWelcome to the POS System \n\n")
    user_login()

main()
