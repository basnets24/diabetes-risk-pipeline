BEGIN {
    FS = OFS = "\t"
    dropped = 0
}

NR == 1 {
    print
    next
}

{
    age = $3
    bmi = $13
    hba1c = $14
    glucose = $15

    if (age > 0 && age <= 120 &&
        bmi > 0 && bmi <= 50 &&
        hba1c >= 3.0 && hba1c <= 15.0 &&
        glucose >= 50 && glucose <= 400) {
        print
    } else {
        dropped++
    }
}

END {
    print "dropped_rows\t" dropped > "logs/quality.log"
}
