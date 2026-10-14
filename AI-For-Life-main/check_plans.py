import json
data = json.load(open('src/plans/plans_simple.json', encoding='utf-8'))
plans = data['plans'] if 'plans' in data else data
for p in plans:
    print('=' * 70)
    print('ID:', p.get('id'), '| City:', p.get('city'), '| Style:', p.get('style'))
    print('Title:', p.get('title'))
    print('Hotel:', (p.get('hotel') or {}).get('name'))
    print('Budget:', (p.get('budgetPerPerson') or {}).get('min'), '-', (p.get('budgetPerPerson') or {}).get('max'))
    for d in p.get('days', []):
        print('  Ngay', d.get('day'), '-', d.get('title'))
        for a in d.get('activities', []):
            loc = a.get('location') or {}
            print('    %-7s %-12s | %-50s | %sđ' % (
                a.get('period', '?'),
                a.get('type', '?'),
                loc.get('name', '?')[:50],
                a.get('costPerPerson', 0)
            ))
    print('costBreakdown:', p.get('costBreakdown'))
    print('estimatedTotalPerPerson:', p.get('estimatedTotalPerPerson'))
    print('travelers:', p.get('travelers'))