from hunter import Hunter

if __name__ == '__main__':
    db = Hunter('All Sets-2012-02-05.db')
    setlist = db.query('SELECT abbreviation FROM sets ORDER BY released')

    for exp in setlist:
        cardlist = db.dbase.execute('SELECT name FROM published JOIN cards ON cards.cardname = published.name WHERE published.expansion = ? AND cards.virtual = ? ORDER BY cards.cn_position, published.name', (exp[0], 'No'))

        y = 1
        for x in cardlist:
            print y, x[0]
            y += 1
