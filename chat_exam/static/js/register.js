function checkRegister() {
        let username = document.getElementsByName("username").value.trim()
        let email = document.getElementsByName("email").value.trim()

        let p1 = document.getElementById("p1").value;
        let p2 = document.getElementById("p2").value;

        if (username === null || username === undefined) {
            alert("Name needs to be filled!")
            return false
        }

        if (email === null || email === undefined) {
            alert("Email needs to be filled!")
            return false
        }

        if (p1 !== p2) {
            alert("Passwords do not match!");
            return false;
        }
        return true;
    }