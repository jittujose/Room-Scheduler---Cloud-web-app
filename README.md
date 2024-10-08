# Room Booking Application

This project is a web application for managing room bookings. It provides features for users to log in, book rooms, view and edit their bookings, and manage rooms. The application uses **Firebase** for authentication and database management.

## Features

- **Login/Logout Service**: Implements Firebase authentication using `firebase-login.js`. The login system must follow the provided examples.
- **Firestore Documents**: 
  - **Room**: Represents rooms available for booking.
  - **Day**: Each room can have zero or more days associated with it.
  - **Booking**: Each day can have zero or more bookings. These documents are linked appropriately without using composite indexes.
- **Add Room Form**: A form for adding new rooms to the database.
- **Available Rooms Display**: A page showing a list of rooms available for booking.

- **Book Room Form**: A separate page where users can book a room for a specific day and time.
- **User Bookings List**: 
  - Form on the main page showing all bookings made by the current user across all rooms.
  - Form on the main page showing all bookings made by the current user for a specific room.
- **Delete Booking**: Each booking in the list has a delete button to remove it.

- **Delete Booking Functionality**: Clicking the delete button removes the selected booking.
- **Edit Booking**: Each booking in the list has an edit button. Editing is done on a separate page with the form prepopulated with current booking details.
- **Delete Room**: Rooms can be deleted by the user who created them, provided there are no existing bookings on the room.

- **Filter by Day**: Ability to filter bookings by a specific day, showing all room bookings for that day.
- **Room Booking Details**: Clicking on a room shows all bookings for that room.
- **UI Design**: User-friendly and intuitive design for ease of use.

## Technologies Used

- **Firebase Authentication** for login/logout
- **Firestore** for data storage
- **HTML/CSS/JavaScript** for frontend development
- **Firebase SDK** for database interactions



