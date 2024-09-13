from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import google.oauth2.id_token;
from google.auth.transport import requests
from google.cloud import firestore
import starlette.status as status
from google.cloud.firestore_v1.base_query import FieldFilter
from datetime import time

app = FastAPI()

firestore_db = firestore.Client()

firebase_request_adapter = requests.Request()

app.mount('/static', StaticFiles(directory='static'), name='static')
templates = Jinja2Templates(directory="templates")

def getUser(user_token):
    user = firestore_db.collection('users').document(user_token['user_id'])
    if not user.get().exists:
        user_data = {
            'name': 'Jittu Jose',
            'room_list': []  
        }
        firestore_db.collection('users').document(user_token['user_id']).set(user_data)

    return user

def validateFirebaseToken(id_token):
    if not id_token:
        return None
    
    user_token = None
    try:
        user_token = google.oauth2.id_token.verify_firebase_token(id_token,firebase_request_adapter)
    except ValueError as err:
        print(str(err))

    return user_token

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    id_token = request.cookies.get("token")
    error_message = "No error here"
    user_token = None
    user = None

    user_token = validateFirebaseToken(id_token)
    print(user_token)
    if not user_token:
        return templates.TemplateResponse('main.html',{'request': request,'user_token':None,'error_message': None, 'user_info':None})
    
    user = getUser(user_token).get()
    # addresses = []
    # for address in user.get('address_list'):
    #     addresses.append(address.get())

    room_data = getRoom("jittu").get()
    rooms = []
    for room in room_data.get('room_list'):
        rooms.append(room.get())
    

    room_bookings = firestore_db.collection('bookingdata').get()
    bookings = []
    allBookings =[]
    for doc in room_bookings:
        oneRoom = doc.to_dict()
        allBookings.append(oneRoom)
        if oneRoom.get('user')==user_token.get('email'):
            bookings.append(oneRoom)
    
    dateArray = []
    dateArray = dateArray_finder(allBookings)
    
    
    return templates.TemplateResponse('main.html',{'request': request,'user_token': user_token,'error_message': error_message, 'user_info':user,'room_list':rooms,'booking_list':bookings,'dateArray':dateArray})



def getRoom(constID):
    roomdata = firestore_db.collection('roomdata').document(constID)
    if not roomdata.get().exists:
        room_data = {
            'room_list':[]
        }
        firestore_db.collection('roomdata').document(constID).set(room_data)
    return roomdata

def getDates(constID):
    datedata = firestore_db.collection('datedata').document(constID)
    if not datedata.get().exists:
        date_data = {
            'date_list':[]
        }
        firestore_db.collection('datedata').document(constID).set(date_data)
    return datedata

def getBooking(constID):
    bookingdata = firestore_db.collection('bookingdata').document(constID)
    if not bookingdata.get().exists:
        booking_data = {
            'booking_list':[]
        }
        firestore_db.collection('bookingdata').document(constID).set(booking_data)
    return bookingdata


def dateArray_finder(array):
    dates = []
    for book in array:
        oneDate = book.get('date')
        if oneDate not in dates and oneDate !=None:
            dates.append(oneDate)
    return dates


@app.post("/add-Room", response_class=RedirectResponse)
async def addRoomPost(request:Request):
    id_token = request.cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')
    
    # pull the form containing our data
    form = await request.form()
    #checking the the new name is existing
    search = form['roomname']
    dummy_data_ref = firestore_db.collection('roomdata')
    query = dummy_data_ref.where('name', '==', search).get()
    if query:
         return RedirectResponse('/', status_code=status.HTTP_302_FOUND)
# create a reference to an address object note that we have not given an ID here
# we are asking firestore to create an ID for us
    room_ref = firestore_db.collection('roomdata').document()
    

# set the data on the address object
    room_ref. set({
        'name': form['roomname'],
        'address1': form['address1'],
        'address2': form['address2'],
        'eircode': form['eircode'],
        'user': form['user'],
        'ref_dates':[],
        'created_by':user_token.get('email')
    })
# add  details to firestore
    
    room = getRoom("jittu")
    rooms = room.get().get('room_list')
    rooms.append(room_ref)
    room.update({'room_list': rooms})


    
# when finished return a redirect with a 302 to force a GET verb
    return RedirectResponse('/', status_code=status.HTTP_302_FOUND)

#Booking Page
@app.get("/book-room", response_class=HTMLResponse)
async def bookRoom(request: Request):
    id_token = request.cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')
    
    roomname=request.query_params.get('roomname')
    

    
    user = getUser(user_token)
    return templates.TemplateResponse('book-room.html',{'request':request,'user_token': user_token,'error_message':None, 'user_info': user.get(),'roomname':roomname})

@app.post("/book-room", response_class=RedirectResponse)
async def bookRoomPost(request:Request):
    id_token = request.cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')
    
    # pull the form containing our data
    form = await request.form()
    
    roomName = form['room_name']
    
    #finding clash in booking
    book_data = getBooking("jittu").get()
    bookings = []
    for book in book_data.get('booking_list'):
        bookings.append(book.get())
    clash = find_clash_book(bookings,roomName,form['bookingDate'],form['startTime'],form['endTime'],None)
    if clash == 0:
        return RedirectResponse('/', status_code=status.HTTP_302_FOUND)
# we are asking firestore to create an ID for us for bookingdata collection
    book_ref = firestore_db.collection('bookingdata').document()
    
    

# set the data on the object
    book_ref. set({
        'date': form['bookingDate'],
        'start_time': form['startTime'],
        'end_time': form['endTime'],
        'user': user_token.get('email'),
        'room_name':roomName,
        'booking_id':book_ref.id
        
    })
# add  details to firestore
    
    room = getBooking("jittu")
    rooms = room.get().get('booking_list')
    rooms.append(book_ref)
    room.update({'booking_list': rooms})

    date_ref = firestore_db.collection('datedata').where('date', '==', form['bookingDate']).get()
    if date_ref:
        # Assuming there is only one document with the given name
        for doc in date_ref:
            date_data = doc.to_dict()
            ref_bookings = date_data.get('ref_booking', [])
            new_booking = book_ref
            ref_bookings.insert(0,new_booking)

            # Update the review field in Firestore
            doc.reference.update({'ref_booking': ref_bookings})
    else:
        date_ref = firestore_db.collection('datedata').document()
        date_ref. set({
        'date': form['bookingDate'],
        'ref_booking':[book_ref], 
        })
# add  details to firestore
        day = getDates("jittu")
        days = day.get().get('date_list')
        days.append(date_ref)
        day.update({'date_list': days})
        
# when finished return a redirect with a 302 to force a GET verb
    return RedirectResponse('/', status_code=status.HTTP_302_FOUND)

@app.post("/filter-booking", response_class=RedirectResponse)
async def filterBooking(request:Request):
    id_token = request.cookies.get("token")
    error_message = "No error here"
    user_token = None
    user = None

    user_token = validateFirebaseToken(id_token)
    print(user_token)
    if not user_token:
        return templates.TemplateResponse('main.html',{'request': request,'user_token':None,'error_message': None, 'user_info':None})
    
    user = getUser(user_token).get()
    # addresses = []
    # for address in user.get('address_list'):
    #     addresses.append(address.get())

    room_data = getRoom("jittu").get()
    rooms = []
    for room in room_data.get('room_list'):
        rooms.append(room.get())
    
    form = await request.form()
    
    roomName = form['room_name']

    room_bookings = firestore_db.collection('bookingdata').get()
    bookings = []
    allBookings =[]
    for doc in room_bookings:
        oneRoom = doc.to_dict()
        allBookings.append(oneRoom)
        if oneRoom.get('user')==user_token.get('email') and oneRoom.get('room_name')==roomName:
            bookings.append(oneRoom)
    
    dateArray = []
    dateArray = dateArray_finder(allBookings)
    
    return templates.TemplateResponse('main.html',{'request': request,'user_token': user_token,'error_message': error_message, 'user_info':user,'room_list':rooms,'booking_list':bookings,'dateArray':dateArray})

# Function to find the index of the object with the specified name
def find_index_by_id(array, name):
    for index, doc_snapshot in enumerate(array):
        # Extract the data from the DocumentSnapshot
        data = doc_snapshot.to_dict()
        # Check if the 'name' attribute matches
        if data.get('booking_id') == name:
            return index
    # Return -1 if the name is not found in any object
    return -1

# Function to find the index of the object with the specified name
def find_index_by_name(array, name):
    for index, doc_snapshot in enumerate(array):
        # Extract the data from the DocumentSnapshot
        data = doc_snapshot.to_dict()
        # Check if the 'name' attribute matches
        if data.get('name') == name:
            return index
    # Return -1 if the name is not found in any object
    return -1

def find_clash_book(array, roomName, date, start_time, end_time,booking_id):
    for book in array:
        if book.get('booking_id')==booking_id:
            continue
        if book.get('room_name') == roomName and book.get('date') == date:
            if start_time >= book.get('start_time') and start_time < book.get('end_time'):
                return 0
            if end_time > book.get('start_time') and end_time <= book.get('end_time'):
                return 0
            if start_time < book.get('start_time') and end_time >= book.get('end_time'):
                return 0
    return 1

@app.post("/delete-booking", response_class=RedirectResponse)
async def deleteBooking(request: Request):
# there should be a token. Validate it and if invalid then redirect back to / as a basic security measure
    id_token = request.cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')

# pull the index from our form
    form = await request. form()
    booking_id = form['booking-id']
    


# pull the list of address objects from the user delete the requested index and update the user
    
    booking = getBooking("jittu")
    bookings = booking.get().get('booking_list')

    #finding index in array to delete
    ev_data = getBooking("jittu").get()
    evcararray = []
    index = -1
    for evcarone in ev_data.get('booking_list'):
        evcararray.append(evcarone.get())

    index=index = find_index_by_id(evcararray, booking_id)
    

    bookings [int(index) ].delete()
    del bookings [int(index) ]
    data = {
        'booking_list': bookings
    }
    booking. update(data)

    # when finished return a redirect with a 302 to force a get verb
    return RedirectResponse('/', status_code=status.HTTP_302_FOUND)

#edit booking 
@app.post("/edit-bookingpage", response_class=HTMLResponse)
async def editBooking(request: Request):
    id_token = request.cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')
    
    #Rooms data
    room_data = getRoom("jittu").get()
    rooms = []
    for room in room_data.get('room_list'):
        rooms.append(room.get())

    form = await request. form()
    booking_id = form['editbooking_id']
    print(booking_id)
    room_bookings = firestore_db.collection('bookingdata').get()
    bookings = []
    for doc in room_bookings:
        oneRoom = doc.to_dict()
        if oneRoom.get('booking_id')==booking_id:
            bookings.append(oneRoom)

    
    user = getUser(user_token)
    return templates.TemplateResponse('edit-booking.html',{'request':request,'user_token': user_token,'error_message':None, 'user_info': user.get(),'bookings':bookings,'rooms':rooms})

@app.post("/edit-booking", response_class=RedirectResponse)
async def editBookingPost(request:Request):
    id_token = request.cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')
    
    # pull the form containing our data
    form = await request. form()

    roomName = form['room_name']
    
    #finding clash in booking
    book_data = getBooking("jittu").get()
    bookings = []
    for book in book_data.get('booking_list'):
        bookings.append(book.get())
    clash = find_clash_book(bookings,roomName,form['bookingDate'],form['startTime'],form['endTime'],form['booking-id'])
    if clash == 0:
        return RedirectResponse('/', status_code=status.HTTP_302_FOUND)
    
    book_id = form['booking-id']

    
    print(book_id)
# we are asking firestore to create an ID for us for bookingdata collection
    book_ref = firestore_db.collection('bookingdata').where('booking_id', '==', book_id).get()    
    
    for book_doc in book_ref:
        book_data = book_doc.to_dict()
        booking_id = book_doc.id

        book_data['date'] = form['bookingDate']
        book_data['start_time'] = form['startTime']
        book_data['end_time'] = form['endTime']
        book_data['room_name'] = form['room_name']
        firestore_db.collection('bookingdata').document(booking_id).set(book_data)
#     date_ref = firestore_db.collection('datedata').where('date', '==', form['bookingDate']).get()
#     if date_ref:
#         # Assuming there is only one document with the given name
#         for doc in date_ref:
#             date_data = doc.to_dict()
#             ref_bookings = date_data.get('ref_booking', [])
#             new_booking = book_ref
#             ref_bookings.insert(0,new_booking)

#             # Update the review field in Firestore
#             doc.reference.update({'ref_booking': ref_bookings})
#     else:
#         date_ref = firestore_db.collection('datedata').document()
#         date_ref. set({
#         'date': form['bookingDate'],
#         'ref_booking':[book_ref], 
#         })
# # add  details to firestore
#         day = getDates("jittu")
#         days = day.get().get('date_list')
#         days.append(date_ref)
#         day.update({'date_list': days})
        
# when finished return a redirect with a 302 to force a GET verb
    return RedirectResponse('/', status_code=status.HTTP_302_FOUND)

#Delete Room
@app.post("/delete-room", response_class=RedirectResponse)
async def deleteRoom(request: Request):
# there should be a token. Validate it and if invalid then redirect back to / as a basic security measure
    id_token = request.cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')

# pull the index from our form
    form = await request. form()
    room_name = form['roomname']
    



    #chekking is there any bookings exist for that room
    room_bookings = firestore_db.collection('bookingdata').get()
    bookings = []
    for doc in room_bookings:
        oneRoom = doc.to_dict()
        bookings.append(oneRoom)
    
    for bookone in bookings:
        if bookone.get('room_name') == room_name:
            return RedirectResponse('/', status_code=status.HTTP_302_FOUND)

    #finding index in array to delete
    room_data = getRoom("jittu").get()
    roomarray = []
    index = -1
    for evcarone in room_data.get('room_list'):
        roomarray.append(evcarone.get())

    index=index = find_index_by_id(roomarray, room_name)
    
    rooming = getRoom("jittu")
    roomings = rooming.get().get('room_list')

    roomings [int(index) ].delete()
    del roomings [int(index) ]
    data = {
        'room_list': roomings
    }
    rooming. update(data)

    # when finished return a redirect with a 302 to force a get verb
    return RedirectResponse('/', status_code=status.HTTP_302_FOUND)

@app.post("/date-filter", response_class=RedirectResponse)
async def filterBookingDate(request:Request):
    id_token = request.cookies.get("token")
    error_message = "No error here"
    user_token = None
    user = None

    user_token = validateFirebaseToken(id_token)
    print(user_token)
    if not user_token:
        return templates.TemplateResponse('main.html',{'request': request,'user_token':None,'error_message': None, 'user_info':None})
    
    user = getUser(user_token).get()
    # addresses = []
    # for address in user.get('address_list'):
    #     addresses.append(address.get())

    room_data = getRoom("jittu").get()
    rooms = []
    for room in room_data.get('room_list'):
        rooms.append(room.get())
    

    room_bookings = firestore_db.collection('bookingdata').get()
    bookings = []
    for doc in room_bookings:
        oneRoom = doc.to_dict()
        bookings.append(oneRoom)

    dateArray = []
    dateArray = dateArray_finder(bookings)
    
    form = await request. form()
    date = form['date_filter']
    filterdBooking =[]
    for oneBook in bookings:
        if oneBook.get('date') == date:
            filterdBooking.append(oneBook)
    
    for i in range(0,len(filterdBooking)):
        for j in range(i,len(filterdBooking)):
            if filterdBooking[i].get('start_time') > filterdBooking[j].get('start_time'):
                temp = filterdBooking[i]
                filterdBooking[i]=filterdBooking[j]
                filterdBooking[j]=temp
        

    return templates.TemplateResponse('main.html',{'request': request,'user_token': user_token,'error_message': error_message, 'user_info':user,'room_list':rooms,'booking_list':filterdBooking,'dateArray':dateArray})

@app.post("/view-book", response_class=RedirectResponse)
async def viewAllBooking(request:Request):
    id_token = request.cookies.get("token")
    error_message = "No error here"
    user_token = None
    user = None

    user_token = validateFirebaseToken(id_token)
    print(user_token)
    if not user_token:
        return templates.TemplateResponse('main.html',{'request': request,'user_token':None,'error_message': None, 'user_info':None})
    
    user = getUser(user_token).get()
    

    room_data = getRoom("jittu").get()
    rooms = []
    for room in room_data.get('room_list'):
        rooms.append(room.get())
    
    form = await request. form()
    roomname = form['roomname']

    room_bookings = firestore_db.collection('bookingdata').get()
    bookings = []
    for doc in room_bookings:
        oneRoom = doc.to_dict()
        bookings.append(oneRoom)

    dateArray = []
    dateArray = dateArray_finder(bookings)
    
    room_bookings = firestore_db.collection('bookingdata').get()
    bookings = []
    for doc in room_bookings:
        oneRoom = doc.to_dict()
        if oneRoom.get('room_name')==roomname:
            bookings.append(oneRoom)
    
    
    
    
    return templates.TemplateResponse('main.html',{'request': request,'user_token': user_token,'error_message': error_message, 'user_info':user,'room_list':rooms,'booking_list':bookings,'dateArray':dateArray})



