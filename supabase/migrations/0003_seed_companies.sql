begin;

insert into public.companies (slug, name, ticker, exchange, sector)
values
    ('reliance-industries', 'Reliance Industries', 'RELIANCE', 'NSE', 'Diversified'),
    ('tcs', 'Tata Consultancy Services', 'TCS', 'NSE', 'Information Technology'),
    ('hdfc-bank', 'HDFC Bank', 'HDFCBANK', 'NSE', 'Financial Services'),
    ('tata-motors', 'Tata Motors', 'TATAMOTORS', 'NSE', 'Automotive'),
    ('larsen-toubro', 'Larsen & Toubro', 'LT', 'NSE', 'Engineering & Construction')
on conflict (slug) do nothing;

commit;
