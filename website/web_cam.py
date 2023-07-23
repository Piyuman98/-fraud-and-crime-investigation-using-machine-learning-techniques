from flask import Flask, render_template, Response
import cv2

app = Flask(__name__)

# Access the video feed
def video_feed():
    video_capture = cv2.VideoCapture(0)

    while True:
        # Read a single frame from the video capture
        ret, frame = video_capture.read()

        # Convert the frame to JPEG format
        ret, jpeg = cv2.imencode('.jpg', frame)

        # Yield the frame as a byte array for the streaming response
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')

# Route for the HTML page
@app.route('/')
def index():
    return render_template('index.html')

# Route for the video streaming
@app.route('/video_feed')
def video_feed_route():
    return Response(video_feed(), mimetype='multipart/x-mixed-replace; boundary=frame')
  

if __name__ == '__main__':
    app.run(debug=True)
