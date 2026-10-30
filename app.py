from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, join_room, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# 存储房间及每轮答案
rooms = {}


@socketio.on('join_room')
def handle_join(data):
    room = data['room']
    join_room(room)
    if room not in rooms:
        rooms[room] = {'words': {}, 'max_rounds': data.get('maxRounds', 10), 'current_round': 1}
    emit('room_joined', {'currentRound': rooms[room]['current_round'], 'maxRounds': rooms[room]['max_rounds']},
         room=room)


@socketio.on('submit_word')
def handle_submit(data):
    room = data['room']
    word = data['word']
    user_id = request.sid

    if room in rooms:
        rooms[room]['words'][user_id] = word

        # 当房间内两个人（或以上）都提交了词汇
        if len(rooms[room]['words']) >= 2:
            all_words = list(rooms[room]['words'].values())
            is_match = (all_words[0] == all_words[1])

            # 广播结果给房间所有人
            emit('round_result', {
                'words': all_words,
                'isMatch': is_match,
                'currentRound': rooms[room]['current_round'],
                'maxRounds': rooms[room]['max_rounds']
            }, room=room)

            # 清空本轮答案，准备下一轮
            rooms[room]['words'] = {}
            rooms[room]['current_round'] += 1


@socketio.on('reset_game')
def handle_reset(data):
    room = data['room']
    if room in rooms:
        rooms[room]['words'] = {}
        rooms[room]['current_round'] = 1
        emit('game_reset', {}, room=room)


import eventlet
eventlet.monkey_patch()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
