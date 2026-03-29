BEGIN {
    FS = OFS = "\t"
}

NR == 1 {
    next
}

{
    bmi = $13
    hba1c = $14
    glucose = $15
    diabetes = $16 + 0

    if (hba1c == 0) {
        next
    }

    ratio = glucose / hba1c

    if (bmi < 18.5) {
        bucket = "Underweight"
    } else if (bmi < 25) {
        bucket = "Normal"
    } else if (bmi < 30) {
        bucket = "Overweight"
    } else {
        bucket = "Obese"
    }

    count[bucket]++
    sum_ratio[bucket] += ratio
    diabetes_sum[bucket] += diabetes
}

END {
    print "bucket", "count", "avg_ratio", "diabetes_rate", "tier"

    for (b in count) {
        avg_ratio = sum_ratio[b] / count[b]
        diabetes_rate = diabetes_sum[b] / count[b]

        if (diabetes_rate > 0.20) {
            tier = "HI"
        } else if (diabetes_rate >= 0.08) {
            tier = "MID"
        } else {
            tier = "LO"
        }

        printf "%s\t%d\t%.4f\t%.4f\t%s\n",
               b, count[b], avg_ratio, diabetes_rate, tier
    }
}
