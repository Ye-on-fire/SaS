from openai import OpenAI
from typing import List, Dict


client = OpenAI(
    base_url='http://10.15.88.73:5031/v1',
    api_key='ollama',  # required but ignored
)

messages : List[Dict] = [
    {"role": "system", "content": '''You are now a healer in a rpg game. 
                                    The player will require you to heal him. 
                                    When he needs a heal, he will tell you \"I need a heal\",or something contains \"need\" and \"heal\" exactly, you heal him.
                                    Then, blame him for his carelessness that he lost so much hp.
                                    When you heal the player.Your replies should be less than 20 words and exactly start with \"You are healed\".'''}
]
print('“勇敢的探险者，我这里有两个选项，一个是提升20点生命值，另一个是提升10点攻击力')
print('如果想要提升攻击力，请输入1；如果想提升攻击力，请输入2.')     
print('当你不需要我的帮助时，按下exit退出对话')
while True:
    user_input = input("")
    # if user_input == '1':
    #     print('还需要别的吗')
    # if user_input == '2':
    #     print('好的')
    if user_input.lower() in [ "exit", "quit"]:
        print("再见")
        break

    messages.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model="llama3.2",      
        messages=messages,    # a list of dictionary contains all chat dictionary
    )

    # 提取模型回复
    assistant_reply = response.choices[0].message.content
    print(f"Llama: {assistant_reply}")

    # 将助手回复添加到对话历史
    messages.append({"role": "assistant", "content": assistant_reply})






'''
messages : List[Dict] = [
    {"role": "system", "content": '不知所云 You are a helpful teaching assitant of computer science lessons, \
                you should help CS freshman with teaching \
                how to use LLM to design and create games better.'}
]


messages : List[Dict] = [
    {"role": "system", "content": "井字棋You are a game player and are playing tic-tac-ton with users.\
Tic-Tac-Toe is a simple two-player game played on a 3x3 grid. Players take turns marking the grid with their respective symbols ('X' or 'O').\
 The objective is to be the first to form a line of three symbols either horizontally, vertically, or diagonally.\
For example, At the start, the grid is empty: \
_ _ _\n\
_ _ _\n\
_ _ _\n\
Player 1 places 'X' in the center:\
_ _ _\n\
_ X _\n\
_ _ _\n"}
]

messages : List[Dict] = [
    {"role": "system", "content": "We are going to play a game now, n\
    and I have an integer in my mind. You can ask me an integer each time, n\
    and I will tell you whether the answer will be larger or smaller than the number asked. n\
    You need to use the minimum number of questions to answer what the answer is. n\
    For example, when the answer in my mind is 200, you can ask 100 and I will tell you that the answer is greater than 100."}
这个是猜数字的，没用]

"这一句是和上面一样的 We are going to play a game now, and I have a number in my mind. You can ask me a number each time, and I will tell you whether the answer will be larger or smaller than the number asked. You need to use the minimum number of questions to answer what the answer is. For example, when the answer in my mind is 200, you can ask 100 and I will tell you that the answer is greater than 100."


"You are a game player and are playing tic-tac-ton with users. \
Tic-Tac-Toe is a simple two-player game played on a 3x3 grid. Players take turns marking the grid with their respective symbols ("X" or "O"). \
 The objective is to be the first to form a line of three symbols either horizontally, vertically, or diagonally.
For example, At the start, the grid is empty: \
_ _ _\n\
_ _ _\n\
_ _ _\n\
Player 1 places "X" in the center:\
_ _ _\n\
_ X _\n\
_ _ _\n"

'''