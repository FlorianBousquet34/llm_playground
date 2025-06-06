// function to check if a number is prime or not
function isNumberPrime(number) {
    let isPrime = true;
    // check if number is equal to 1
    if (number === 1) {
        isPrime = false;
    // check if number is greater than 1
    } else if (number > 1) {
        // looping through 2 to number/2
        for (let i = 2; i <= number/2; i++) {
            if (number % i == 0) {
                isPrime = false;
                break;
            }
        }
    }
    // check if number is less than 1
    else {
        isPrime = false;
    }
    return isPrime;
}

export { isNumberPrime };