package demo

const pathSampleSeconds = 0.2

func sampleTickStep(tickRate float64) int {
	step := int(tickRate * pathSampleSeconds)
	if step < 1 {
		return 1
	}
	return step
}

