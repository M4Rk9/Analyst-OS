-- Reviewed financial facts require explicit printed numbers, not dash-as-zero.
-- Existing unverified evidence remains intact. Validating this constraint fails
-- atomically if any previously verified row has an unsupported display amount.
-- No source/fact approvals, values, preferences or receipts are changed.
begin;

alter table public.financial_facts
    add constraint facts_explicit_reported_amount check (
        quality_status <> 'verified'
        or (
            raw_value_text is not null
            and case
                when regexp_replace(
                    translate(raw_value_text, 'ϬϭϮϯϰϱϲϳϴϵ', '0123456789'),
                    '[,[:space:]]', '', 'g'
                ) ~ '^(-?[0-9]+([.][0-9]+)?|[(][0-9]+([.][0-9]+)?[)])$'
                then (
                    case
                        when left(regexp_replace(
                            translate(raw_value_text, 'ϬϭϮϯϰϱϲϳϴϵ', '0123456789'),
                            '[,[:space:]]', '', 'g'
                        ), 1) = '('
                        then '-' || trim(both '()' from regexp_replace(
                            translate(raw_value_text, 'ϬϭϮϯϰϱϲϳϴϵ', '0123456789'),
                            '[,[:space:]]', '', 'g'
                        ))
                        else regexp_replace(
                            translate(raw_value_text, 'ϬϭϮϯϰϱϲϳϴϵ', '0123456789'),
                            '[,[:space:]]', '', 'g'
                        )
                    end
                )::numeric = raw_value
                else false
            end
        )
    );

commit;
