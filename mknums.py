from hunter import Hunter

if __name__ == '__main__':
    db = Hunter('All Sets-2012-04-26.db')

    db.dbase.execute('CREATE INDEX IF NOT EXISTS cnames ON cards (cardname);')
    db.dbase.execute('CREATE INDEX IF NOT EXISTS pubexp ON published (expansion);')
    db.dbase.execute('CREATE INDEX IF NOT EXISTS pubnames ON published (name);')

    setlist = db.query('SELECT abbreviation FROM sets ORDER BY released')

    # hack in changes for Planar Chaos' bullshit WRT split cards
    for a in ['Boom // Bust', 'Dead // Gone', 'Rough // Tumble']:
        db.dbase.execute('UPDATE cards SET cn_position = 54 WHERE cards.cardname = ?', (a,) )

    for exp in setlist:
        # special case for time spiral
        if exp[0] == 'TSP':
            cardlist = db.dbase.execute('SELECT DISTINCT published.name,published.rarity FROM published JOIN cards ON cards.cardname = published.name WHERE published.expansion = ? AND cards.virtual = ? ORDER BY CASE published.rarity WHEN ? THEN 2 ELSE 1 END,cards.cn_position, published.name', (exp[0], 'No', 'S'))

        # all other sets
        else:
            cardlist = db.dbase.execute('SELECT DISTINCT published.name FROM published JOIN cards ON cards.cardname = published.name WHERE published.expansion = ? AND cards.virtual = ? ORDER BY cards.cn_position, published.name', (exp[0], 'No'))

        y = 1
        for x in cardlist:
            print y, x[0]
            y += 1
