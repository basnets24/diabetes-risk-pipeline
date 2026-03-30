BEGIN {
    FS = "\t"
    OFS = "\t"
}

NR == 1 {
    for (i = 1; i <= NF; i++) {
        h[$i] = i
    }
    print "hypertension", "heart_disease", "count", "diabetes_rate", "mean_bmi", "min_bmi", "max_bmi", "mean_hba1c", "min_hba1c", "max_hba1c", "mean_glucose", "min_glucose", "max_glucose", "outlier_count"
    next
}

{
    hyp = $h["hypertension"]
    heart = $h["heart_disease"]
    bmi = $h["bmi"]
    hba1c = $h["hbA1c_level"]
    glucose = $h["blood_glucose_level"]
    diabetes = $h["diabetes"]

    if (hyp == "" || heart == "" || bmi == "" || hba1c == "" || glucose == "" || diabetes == "") next

    key = hyp OFS heart

    count[key]++
    sum_bmi[key] += bmi
    sum_hba1c[key] += hba1c
    sum_glucose[key] += glucose

    if (!(key in min_bmi) || bmi < min_bmi[key]) min_bmi[key] = bmi
    if (!(key in max_bmi) || bmi > max_bmi[key]) max_bmi[key] = bmi

    if (!(key in min_hba1c) || hba1c < min_hba1c[key]) min_hba1c[key] = hba1c
    if (!(key in max_hba1c) || hba1c > max_hba1c[key]) max_hba1c[key] = hba1c

    if (!(key in min_glucose) || glucose < min_glucose[key]) min_glucose[key] = glucose
    if (!(key in max_glucose) || glucose > max_glucose[key]) max_glucose[key] = glucose

    if (diabetes == 1) diabetes_count[key]++

    if (hba1c > 8.0 || glucose > 200) outlier_count[key]++
}

END {
    for (key in count) {
        rate = diabetes_count[key] / count[key]
        mean_bmi = sum_bmi[key] / count[key]
        mean_hba1c = sum_hba1c[key] / count[key]
        mean_glucose = sum_glucose[key] / count[key]

        printf "%s\t%d\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\n",
            key,
            count[key],
            rate,
            mean_bmi, min_bmi[key], max_bmi[key],
            mean_hba1c, min_hba1c[key], max_hba1c[key],
            mean_glucose, min_glucose[key], max_glucose[key],
            outlier_count[key] + 0
    }
}
