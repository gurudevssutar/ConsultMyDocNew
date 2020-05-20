from flask import Flask

def Articles():
    articles=[
        {
            'id':1,
            'title':'Corona Warrior',
            'body':'All of a sudden in our busy world....',
            'author':'Gurudev'
        },
        {
            'id':2,
            'title':'Love',
            'body':'Most beautiful but unfortunately crippling for most people.',
            'author':'Sadhguru'
        },
        {
            'id':3,
            'title':'Tu phodega',
            'body':'Hustle 24 by 7 day in and day out and make the maximum use of your potential.',
            'author':'Aman Dhattarwal'
        }
    ]
    return articles
