BEGIN {
    FS = "\t"
    OFS = "\t"
}

NR == 1 {
    for (i = 1; i <= NF; i++) {
        gsub(/^[ \t]+|[ \t]+$/, "", $i)
        h[$i] = i
    }
    next
}

{
    year = $h["year"]
    bmi = $h["bmi"]
    glucose = $h["blood_glucose_level"]
    diabetes = $h["diabetes"]

    if (year == "" || bmi == "" || glucose == "" || diabetes == "") next

    count[year]++
    sum_bmi[year] += bmi
    sum_glucose[year] += glucose

    if (diabetes == 1) {
        diabetes_count[year]++
    }
}

END {
    for (y in count) {
        rate = diabetes_count[y] / count[y]
        avg_b = sum_bmi[y] / count[y]
        avg_g = sum_glucose[y] / count[y]

        printf "%s\t%d\t%.4f\t%.4f\t%.4f\n", y, count[y], rate, avg_b, avg_g
    }
}
