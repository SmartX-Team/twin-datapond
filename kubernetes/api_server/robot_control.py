import json
from flask import Flask, request, jsonify
from confluent_kafka import Producer

class CommandRequest:
    def __init__(self, command: str, duration: float):
        self.command = command
        self.duration = duration

class RobotControllerByCommands:
    def __init__(self, config_path='None'):
        self.config_path = config_path
        self.producer = None
        self.topic = None
        self._load_config_and_initialize()

    def _load_config_and_initialize(self):
        """Load configuration and initialize the Kafka producer."""
        self.producer = Producer({
            'bootstrap.servers': '10.80.0.3:9094'
        })
        self.topic = 'virtual-joystick-api-0950'

    def send_command(self, command, duration):
        """Send robot control command to Kafka topic."""
        command_message = json.dumps({
            'command': command,
            'duration': duration
        })
        self.producer.produce(self.topic, command_message, callback=self.delivery_report)
        self.producer.flush()  # Ensure delivery by calling flush()
        print(f"Sent command to {self.topic}: {command_message}")

    def delivery_report(self, err, msg):
        """Report the status of message delivery."""
        if err is not None:
            print(f'Message delivery failed: {err}')
        else:
            print(f'Message delivered to {msg.topic()} [{msg.partition()}]')

    def close_producer(self):
        """Clean up the producer."""
        self.producer.flush()
        print("Kafka producer closed.")

# Create a Flask application instance
app = Flask(__name__)
robot_controller = RobotControllerByCommands()  # Initialize the robot controller

@app.route('/send_command', methods=['POST'])
def send_command():
    """Send command via REST API endpoint."""
    try:
        data = request.get_json()
        command = data.get('command')
        duration = data.get('duration')

        if not command or not isinstance(duration, (float, int)):
            return jsonify({"status": "error", "message": "Invalid input"}), 400

        robot_controller.send_command(command, float(duration))
        return jsonify({"status": "success", "message": "Command sent successfully"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.teardown_appcontext
def shutdown_session(exception=None):
    """Close Kafka producer when the application context is torn down."""
    robot_controller.close_producer()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
