# EducationHub, A Free Alternative Educational Platform

## Project Overview

This project aims to provide a free, open-source educational platform for organizations in need. Whether for nonprofits, educational institutions, or community-driven initiatives, this platform offers an accessible solution for hosting classes, facilitating teacher-student communication, and managing educational resources.

### Features

- **Course Information**: Display essential course details.
- **Video Meetings**: Integrated with Jitsi Meet for seamless online classes.
- **Chat with Teacher**: Real-time messaging between students and teachers.
- **Notes and Worksheets**: Upload and download notes and other educational materials.
- **Firebase Integration**: Backend support for real-time database and storage.
- **Customization**: Easily customizable to meet specific organizational needs.

## Getting Started

### Prerequisites

- Python 3.x
- Flask
- Firebase account
- Firebase Admin SDK credentials

### Setup

1. **Clone the Repository**
    ```bash
    git clone https://github.com/mrithunjay26/EducationHub.git
    cd EducationHub
    ```

2. **Install Python Dependencies**
    ```bash
    pip install firebase_admin, flask
    ```

3. **Configure Firebase**

    - Go to the [Firebase Console](https://console.firebase.google.com/).
    - Create a new project.
    - In the project settings, generate a new service account key (JSON file).
    - Download the JSON file and place it in the root directory of the project.

4. **Set Up Environment Variables**

    - Rename `.env.example` to `.env`.
    - Update the `.env` file with your Firebase project details, including the path to your service account JSON file.

5. **Run the Application**
    ```bash
    flask run
    ```

    The application will be accessible at `http://127.0.0.1:5000/`.

### Firebase Setup

1. **Realtime Database**
    - Navigate to the Realtime Database section in Firebase.
    - Set up the database rules as needed for your project.

2. **Storage**
    - Go to the Storage section in Firebase.
    - Set up your storage buckets for uploading and downloading files.

### Using the Platform

- **Session Management**: The platform uses session storage to keep track of user sessions. Ensure users are logged in before accessing specific features.
- **Customizing for Your Organization**: The platform is designed to be easily customizable. Adjust the HTML, CSS, and JavaScript files to match your organization's branding and needs.

## Contributing

Contributions are welcome! Please fork this repository, make your changes, and submit a pull request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

