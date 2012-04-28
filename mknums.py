from hunter import Hunter

if __name__ == '__main__':
    db = Hunter('All Sets-2012-02-05.db')

    db.dbase.execute('CREATE INDEX IF NOT EXISTS cnames ON cards (cardname);')
    db.dbase.execute('CREATE INDEX IF NOT EXISTS pubexp ON published (expansion);')
    db.dbase.execute('CREATE INDEX IF NOT EXISTS pubnames ON published (name);')

    setlist = db.query('SELECT abbreviation FROM sets ORDER BY released')

    for exp in setlist:
        cardlist = db.dbase.execute('SELECT published.name FROM published JOIN cards ON cards.cardname = published.name WHERE published.expansion = ? AND cards.virtual = ? ORDER BY cards.cn_position, published.name', (exp[0], 'No'))

        y = 1
        for x in cardlist:
            print y, x[0]
            y += 1
