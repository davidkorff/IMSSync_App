-- Check if the email exists in tblproducercontacts
SELECT TOP 10
    ProducerContactGUID,
    ProducerLocationGUID,
    fname,
    lname,
    email,
    statusid
FROM tblproducercontacts
WHERE email = 'CAFinver@Wholesure.com'
ORDER BY ProducerContactGUID DESC;

-- Check what active producer emails exist (for testing)
SELECT TOP 20
    ProducerContactGUID,
    ProducerLocationGUID,
    fname + ' ' + lname AS FullName,
    email,
    statusid
FROM tblproducercontacts
WHERE statusid = 1
    AND email IS NOT NULL
    AND email != ''
ORDER BY ProducerContactGUID DESC;

-- Check if there's a producer with a similar name
SELECT TOP 10
    ProducerContactGUID,
    ProducerLocationGUID,
    fname + ' ' + lname AS FullName,
    email,
    statusid
FROM tblproducercontacts
WHERE (fname LIKE '%CAF%' OR lname LIKE '%CAF%' OR email LIKE '%CAF%')
   OR (fname LIKE '%Wholesure%' OR lname LIKE '%Wholesure%' OR email LIKE '%Wholesure%')
ORDER BY statusid DESC, ProducerContactGUID DESC;