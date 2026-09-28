#!/usr/bin/env python3
"""Add connected synthetic property management and P&C insurance marts."""
import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

PRODUCTS = [
    ("MRH", "Multirisque habitation occupant", "HABITATION"),
    ("PNO", "Propriétaire non occupant", "HABITATION"),
    ("GLI", "Garantie loyers impayés", "LOYERS"),
    ("MRI", "Multirisque immeuble", "IMMEUBLE"),
    ("DO", "Dommages ouvrage", "CONSTRUCTION"),
    ("RCD", "Responsabilité civile décennale", "CONSTRUCTION"),
    ("MRP", "Multirisque professionnelle", "PROFESSIONNEL"),
    ("RC_PRO", "Responsabilité civile professionnelle", "PROFESSIONNEL"),
    ("AUTO_FLOTTE", "Flotte automobile professionnelle", "AUTOMOBILE"),
    ("VACANCE", "Perte de loyers entre deux locataires", "LOYERS"),
    ("CARENCE", "Perte de loyers avant la première location", "LOYERS"),
    ("PJ", "Protection juridique autonome", "PROTECTION_JURIDIQUE"),
]
GUARANTEES = {
    "MRH": ("DEGATS_EAUX", "INCENDIE", "VOL", "BRIS_GLACE", "RC_VIE_PRIVEE"),
    "PNO": ("DEGATS_EAUX", "INCENDIE", "RC_PROPRIETAIRE", "PERTE_LOYERS_APRES_SINISTRE"),
    "GLI": ("LOYERS_IMPAYES", "DEGRADATIONS_LOCATIVES", "FRAIS_CONTENTIEUX",
            "PROTECTION_JURIDIQUE", "OCCUPATION_ILLICITE"),
    "MRI": ("DEGATS_EAUX", "INCENDIE", "CAT_NAT", "RC_IMMEUBLE", "BRIS_TECHNIQUE"),
    "DO": ("DOMMAGES_OUVRAGE",),
    "RCD": ("RESPONSABILITE_DECENNALE",),
    "MRP": ("DEGATS_EAUX", "INCENDIE", "PERTE_EXPLOITATION"),
    "RC_PRO": ("RESPONSABILITE_CIVILE",),
    "AUTO_FLOTTE": ("RESPONSABILITE_CIVILE", "DOMMAGES_VEHICULE"),
    "VACANCE": ("VACANCE_LOCATIVE",),
    "CARENCE": ("CARENCE_LOCATIVE",),
    "PJ": ("PROTECTION_JURIDIQUE",),
}


class Writer:
    def __init__(self, directory):
        self.directory = directory
        self.count = Counter()

    def write(self, name, cols, rows):
        with (self.directory/(name+'.csv')).open('w',newline='',encoding='utf-8') as f:
            w=csv.writer(f,lineterminator='\n'); w.writerow(cols)
            for r in rows:
                assert len(r)==len(cols),(name,r)
                w.writerow(r); self.count[name]+=1


def main():
    p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True)
    p.add_argument('--max-total-rows',type=int,default=2400000)
    a=p.parse_args();d=a.data
    old=json.loads((d/'manifest.json').read_text(encoding='utf8'))
    rental=old['files']['fact_encaissement.csv']['rows']//48
    programmes=old['files']['dim_programme.csv']['rows']
    # Only append synthetic tables with stable keys to the certified release.
    w=Writer(d)
    w.write('dim_entreprise',['entreprise_id','nom','type_entreprise','fictive'],[
        ('ENT0001','Veloriax Habitat','ASSUREUR_ET_GARANT_SIMULE',1)])
    w.write('dim_produit_assurance',['produit_code','libelle','famille'],PRODUCTS)
    w.write('dim_garantie',['garantie_code','famille_sinistre'],[
        (g,'LOYERS' if g in ('LOYERS_IMPAYES','VACANCE_LOCATIVE','CARENCE_LOCATIVE',
                            'PERTE_LOYERS_APRES_SINISTRE','OCCUPATION_ILLICITE')
         else 'JURIDIQUE' if g=='PROTECTION_JURIDIQUE' else 'DOMMAGES_OU_RC')
        for g in sorted(set(sum((list(v) for v in GUARANTEES.values()),[])))])

    def contracts():
        for yr in range(2023,2027):
            for i in range(1,rental+1):
                lot=f'L{i:07d}'
                for prod in ('MRH','PNO','GLI','VACANCE','CARENCE','PJ'):
                    if prod=='GLI' and i%4!=2: continue
                    if prod=='VACANCE' and i%5!=1: continue
                    if prod=='CARENCE' and (i%5!=0 or yr!=2023): continue
                    if prod=='PJ' and i%7: continue
                    policy=f'POL_{prod}_{yr}_{i:06d}'
                    annual={'MRH':21000,'PNO':14500,'GLI':29000,'VACANCE':12500,
                            'CARENCE':10000,'PJ':7500}[prod]+i%80*100
                    end=f'{yr}-03-31' if prod=='CARENCE' else f'{yr}-12-31'
                    yield (policy,prod,lot,'','','ENT0001',f'{yr}-01-01',end,annual,
                           'SIMULATION','ACTIF','REL_20260927_2312')
            for prog in range(1,programmes+1):
                prod='MRI' if prog<=40 else 'DO'
                if prod=='DO' and yr!=2023: continue
                policy=f'POL_{prod}_{yr}_{prog:04d}'
                annual=260000+prog*1200 if prod=='MRI' else 580000+prog*1000
                yield (policy,prod,'',f'P{prog:04d}','','ENT0001',f'{yr}-01-01',f'{yr}-12-31',annual,
                       'SIMULATION','ACTIF','REL_20260927_2312')
            for prod,n in (('RCD',90),('MRP',140),('RC_PRO',180),('AUTO_FLOTTE',70)):
                for j in range(1,n+1):
                    policy=f'POL_{prod}_{yr}_{j:04d}'
                    yield (policy,prod,'','',f'PRO{(j-1)%32+1:03d}','ENT0001',f'{yr}-01-01',f'{yr}-12-31',
                           18000+j*83,'SIMULATION','ACTIF','REL_20260927_2312')

    cols=['contrat_id','produit_code','lot_id','programme_id','professionnel_id','assureur_id','date_effet','date_echeance',
          'prime_annuelle_centimes','systeme_source','statut','release_id']
    w.write('dim_contrat_assurance',cols,contracts())

    def policies():
        with (d/'dim_contrat_assurance.csv').open(newline='',encoding='utf8') as f:
            yield from csv.DictReader(f)

    def guarantees():
        for r in policies():
            for g in GUARANTEES[r['produit_code']]:
                yield (r['contrat_id'],g,'2023-01-01' if r['produit_code']=='DO' else r['date_effet'],
                       r['date_echeance'],50000000 if g=='LOYERS_IMPAYES' else 250000000,
                       0 if g=='LOYERS_IMPAYES' else 15000)
    w.write('pont_contrat_garantie',['contrat_id','garantie_code','couvert_du','couvert_au',
        'plafond_centimes','franchise_centimes'],guarantees())

    def premiums():
        for r in policies():
            annual=int(r['prime_annuelle_centimes']);yr=int(r['date_effet'][:4])
            last_quarter=(int(r['date_echeance'][5:7])-1)//3+1
            for q in range(1,last_quarter+1):
                amt=annual//4 if q<4 else annual-3*(annual//4)
                yield (f"PR_{r['contrat_id']}_Q{q}",r['contrat_id'],f'{yr}-{(q-1)*3+1:02d}-01',
                       amt,amt,'EMISE_ET_ACQUISE',r['release_id'])
    w.write('fact_prime_trimestrielle',['prime_ligne_id','contrat_id','trimestre_debut',
        'prime_emise_centimes','prime_acquise_centimes','statut','release_id'],premiums())

    # Each GLI claim corresponds to a real generated missed-payment lot-month.
    def claim_records():
        for i in range(1,rental+1):
            if i%4==2:
                for m in range(48):
                    if not (i%5==0 and m<3) and (i*37+m*19)%100<87 and (i*13+m)%67==0:
                        if (i+m)%3: continue
                        yr=2023+m//12; mon=1+m%12
                        claim_id=f'SIN_GLI_{i:06d}_{m:02d}'
                        yield (claim_id,f'POL_GLI_{yr}_{i:06d}',f'L{i:07d}',
                               'LOYERS_IMPAYES',date(yr,mon,12).isoformat(),
                               date(yr,mon,19).isoformat(),170000+i%70*1000,'GLI')
            if i%17==0:
                yr=2023+i%4;mon=1+i%12
                prod='MRH' if i%3 else 'PNO';g='DEGATS_EAUX' if i%5 else 'INCENDIE'
                yield (f'SIN_{prod}_{i:06d}',f'POL_{prod}_{yr}_{i:06d}',f'L{i:07d}',g,
                       date(yr,mon,4).isoformat(),date(yr,mon,10).isoformat(),
                       90000+(i*731)%900000,prod)
            if i%101==1 and i%5==1:
                for m in range(1,47):
                    if (i*37+(m-1)*19)%100<87 and (i*37+m*19)%100>=87 and (i*37+(m+1)*19)%100<87:
                        yr=2023+m//12;mon=1+m%12
                        yield (f'SIN_VAC_{i:06d}_{m:02d}',f'POL_VACANCE_{yr}_{i:06d}',
                               f'L{i:07d}','VACANCE_LOCATIVE',date(yr,mon,5).isoformat(),
                               date(yr,mon,12).isoformat(),120000,'VACANCE')
                        break
            if i%215==0:
                yield (f'SIN_CAR_{i:06d}',f'POL_CARENCE_2023_{i:06d}',f'L{i:07d}',
                       'CARENCE_LOCATIVE','2023-02-01','2023-02-09',180000,'CARENCE')
        for prog in range(1,41):
            if prog%5==0:
                yr=2023+prog%4
                yield (f'SIN_MRI_{prog:04d}',f'POL_MRI_{yr}_{prog:04d}','',
                       'DEGATS_EAUX',f'{yr}-07-10',f'{yr}-07-18',210000+prog*8000,'MRI')

    claims=list(claim_records())
    w.write('fact_sinistre',['sinistre_id','contrat_id','lot_id','garantie_code',
        'date_survenance','date_declaration','cout_estime_centimes','produit_code'],claims)

    def movements():
        for claim_id,policy,lot,g,occ,dec,estimate,prod in claims:
            declared=date.fromisoformat(dec); settled=(sum(map(ord,claim_id))%7 != 0)
            yield (f'MVT_{claim_id}_1',claim_id,dec,'OUVERTURE',0,estimate,0)
            if settled:
                pay=estimate*8//10; rec=estimate//20 if prod!='GLI' else 0
                on=min(date(2026,12,31),declared+timedelta(days=26))
                yield (f'MVT_{claim_id}_2',claim_id,on.isoformat(),'REGLEMENT',pay,-estimate,rec)
    w.write('fact_mouvement_sinistre',['mouvement_id','sinistre_id','date_mouvement',
        'type_mouvement','paye_delta_centimes','provision_delta_centimes','recours_delta_centimes'],movements())

    def month_date(m): return date(2023+m//12,1+m%12,1)
    def occupied(i,m): return not (i%5==0 and m<3) and (i*37+m*19)%100<87
    def episodes(i):
        begin=None
        for m in range(49):
            is_on=m<48 and occupied(i,m)
            if is_on and begin is None: begin=m
            if not is_on and begin is not None:
                yield (begin,m-1)
                begin=None

    def leases():
        for i in range(1,rental+1):
            for episode,(first,last) in enumerate(episodes(i),1):
                protection=('VISALE' if i%4==0 and episode==1 else
                            'GLI' if i%4==2 else 'AUCUNE')
                yield (f'BAIL_{i:06d}_{episode:02d}',f'L{i:07d}',
                       month_date(first).isoformat(),
                       (month_date(last+1)-timedelta(days=1)).isoformat(),
                       28+(i*17)%112,protection,'HABITATION')
    w.write('dim_bail',['bail_id','lot_id','date_debut','date_fin','surface_m2',
        'protection_impayes','nature_bail'],leases())

    def occupation():
        for i in range(1,rental+1):
            lookup={m:f'BAIL_{i:06d}_{episode:02d}'
                    for episode,(first,last) in enumerate(episodes(i),1)
                    for m in range(first,last+1)}
            first_lease=min(lookup)
            for m in range(48):
                status=('OCCUPE' if m in lookup else
                        'CARENCE' if m<first_lease else 'VACANCE')
                yield (f'OCC_{i:06d}_{m:02d}',f'L{i:07d}',month_date(m).isoformat(),
                       lookup.get(m,''),status,28+(i*17)%112)
    w.write('fact_occupation_mensuelle',['occupation_id','lot_id','mois','bail_id',
        'statut_occupation','surface_m2'],occupation())

    # Visale is a surety scheme, not an insurance policy or a premium.
    def visale():
        for i in range(4,rental+1,4):
            first,last=next(episodes(i))
            effect=month_date(first)
            expiry=min(month_date(last+1)-timedelta(days=1),
                       date(effect.year+3,effect.month,1)-timedelta(days=1))
            yield (f'VIS_{i:06d}',f'BAIL_{i:06d}_01',f'L{i:07d}','VISALE',
                   effect.isoformat(),expiry.isoformat(),'ACTION_LOGEMENT',
                   '18_30_SIMULE','VALIDE_SIMULE')
    w.write('dim_cautionnement',['cautionnement_id','bail_id','lot_id','dispositif',
        'date_effet','date_fin','organisme','profil_eligibilite_simule','statut'],visale())

    def dpe():
        grades='AABBBCCCDDDEEFG'
        for i in range(1,rental+1):
            grade=grades[(i*7)%len(grades)]
            yield (f'DPE_{i:06d}',f'L{i:07d}','2023-01-01',grade,
                   45+(i*23)%440,4+(i*5)%105,'SIMULATION_SANS_NUMERO_ADEME')
    w.write('fact_dpe',['diagnostic_id','lot_id','date_diagnostic','classe_energie',
        'conso_kwh_m2_an','ges_kgco2_m2_an','origine'],dpe())

    def travaux():
        for i in range(1,rental+1,3):
            yr=2023+i%4
            budget=100000+(i*197)%400000
            yield (f'TRX_{i:06d}',f'L{i:07d}',f'{yr}-{1+i%12:02d}-01',
                   'RENOVATION_ENERGETIQUE' if i%3 else 'ENTRETIEN',budget,
                   budget*7//10,'TERMINE' if i%5 else 'EN_COURS')
    w.write('fact_travaux',['travaux_id','lot_id','date_commande','type_travaux',
        'budget_centimes','realise_centimes','statut'],travaux())

    def valuations():
        for yr in range(2023,2027):
            for prog in range(1,programmes+1):
                if prog>40: continue
                yield (f'VAL_{yr}_{prog:04d}',f'P{prog:04d}',f'{yr}-12-31',
                       400000000+prog*2100000+(yr-2023)*5000000,
                       'EXPERTISE_SYNTHETIQUE')
    w.write('fact_valorisation',['valorisation_id','programme_id','date_valeur',
        'valeur_centimes','methode'],valuations())

    # Intermediary business: mandates and client funds, distinct from insurance premiums.
    w.write('dim_professionnel',['professionnel_id','region_code','activite_principale'],
        ((f'PRO{i:03d}',('IDF','ARA','PACA','BRE')[i%4],
          ('GESTION','SYNDIC','TRANSACTION')[i%3]) for i in range(1,33)))
    def mandates():
        for prog in range(1,programmes+1):
            yield (f'MAN{prog:04d}',f'PRO{(prog-1)%32+1:03d}',f'P{prog:04d}',
                   'GESTION_LOCATIVE' if prog<=40 else 'TRANSACTION',
                   '2023-01-01','2026-12-31','ACTIF')
    w.write('dim_mandat',['mandat_id','professionnel_id','programme_id','activite',
        'date_debut','date_fin','statut'],mandates())
    def financial_guarantees():
        for yr in range(2023,2027):
            for pro in range(1,33):
                yield (f'GF_{yr}_{pro:03d}',f'PRO{pro:03d}','ENT0001',f'{yr}-01-01',f'{yr}-12-31',
                       30000000,'AVEC_MANIEMENT_FONDS','GARANTIE_FINANCIERE_SIMULEE')
    w.write('dim_garantie_financiere',['garantie_financiere_id','professionnel_id','garant_id',
        'date_effet','date_fin','plafond_centimes','regime','nature'],financial_guarantees())
    def fund_moves():
        for month in range(48):
            yr=2023+month//12; mon=1+month%12
            for prog in range(1,programmes+1):
                amount=180000+prog%19*1500
                yield (f'FREC_{month:02d}_{prog:04d}',f'MAN{prog:04d}',
                       f'{yr}-{mon:02d}-05','RECEPTION_FONDS_CLIENT',amount)
                yield (f'FVER_{month:02d}_{prog:04d}',f'MAN{prog:04d}',
                       f'{yr}-{mon:02d}-24','VERSEMENT_MANDANT',-amount+10000)
    w.write('fact_mouvement_fonds',['mouvement_fonds_id','mandat_id','date_mouvement',
        'type_mouvement','montant_signe_centimes'],fund_moves())

    # Extend the fault catalogue, with no corrupt rows in the certified release.
    with (d/'ops_incident_scenario.csv').open(newline='',encoding='utf8') as f:
        old_faults=list(csv.reader(f))
    old_faults.extend([
        ['INC004','2026-09-28 11:02:10','dim_contrat_assurance','COUVERTURE_EXPIREE','BLOQUER_PROMOTION'],
        ['INC005','2026-09-28 11:30:10','fact_sinistre','DOUBLE_DECLARATION','BLOQUER_PROMOTION'],
        ['INC006','2026-09-28 12:02:10','fact_prime_trimestrielle','TRIMESTRE_ABSENT','BLOQUER_PROMOTION'],
        ['INC007','2026-09-28 12:30:10','dim_objectif_historise','REVISION_CHEVAUCHANTE','BLOQUER_PROMOTION']])
    old_faults.extend([
        ['INC008','2026-09-28 13:02:10','dim_cautionnement','VISALE_GLI_CHEVAUCHEMENT','BLOQUER_PROMOTION'],
        ['INC009','2026-09-28 13:30:10','fact_mouvement_fonds','FONDS_NON_RESTITUES','BLOQUER_PROMOTION'],
        ['INC010','2026-09-28 14:02:10','dim_garantie_financiere','PLAFOND_INSUFFISANT','BLOQUER_PROMOTION']])
    with (d/'ops_incident_scenario.csv').open('w',newline='',encoding='utf8') as f:
        csv.writer(f,lineterminator='\n').writerows(old_faults)

    files={}
    for path in sorted(d.glob('*.csv')):
        with path.open(newline='',encoding='utf8') as f: rows=sum(1 for _ in f)-1
        files[path.name]={'rows':rows,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    old['files']=files; old['total_rows']=sum(x['rows'] for x in files.values())
    old['model_version']='2-immo-assurance';old.pop('acronym_note',None)
    if old['total_rows']>a.max_total_rows:
        raise SystemExit(f"{old['total_rows']:,} exceeds --max-total-rows {a.max_total_rows:,}")
    (d/'manifest.json').write_text(json.dumps(old,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'total_rows':old['total_rows'],'new_tables':dict(w.count)},ensure_ascii=False))

if __name__=='__main__': main()
