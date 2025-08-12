-- Option 1: Update an existing producer to have this email
-- First, find a producer that should have this email (replace the GUID with the correct one)
/*
UPDATE tblproducercontacts
SET email = 'CAFinver@Wholesure.com'
WHERE ProducerContactGUID = 'YOUR-PRODUCER-GUID-HERE'
    AND statusid = 1;
*/

-- Option 2: Insert a new producer contact with this email
-- Note: You'll need to provide appropriate values for all required fields
/*
INSERT INTO tblproducercontacts (
    ProducerContactGUID,
    ProducerLocationGUID,
    fname,
    lname,
    email,
    statusid,
    -- Add other required fields here based on your table structure
)
VALUES (
    NEWID(), -- Generate new GUID
    'YOUR-LOCATION-GUID-HERE', -- Need to provide valid location GUID
    'CAF',
    'Inver',
    'CAFinver@Wholesure.com',
    1,
    -- Add other required values here
);
*/

-- Option 3: Find the producer by name and update their email
-- This finds producers with similar names and updates their email
/*
UPDATE tblproducercontacts
SET email = 'CAFinver@Wholesure.com'
WHERE fname + ' ' + lname IN ('CAF Inver', 'C.A.F. Inver', 'CAFinver')
    AND statusid = 1;
*/